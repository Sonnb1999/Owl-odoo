# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
from typing import Annotated, Any, List

from a2wsgi import ASGIMiddleware

from odoo import _, api, fields, models, tools
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader

from ..dependencies import (odoo_env, fastapi_endpoint_impl)
from ..routers import curd_router, partner_router
from fastapi.middleware.cors import CORSMiddleware
from .. import dependencies


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    th_access_ids = fields.One2many('th.access.url', 'th_fastapi_id')
    th_save_log_ids = fields.One2many('th.save.log', 'th_fastapi_id')
    th_auth_method = fields.Selection([("api_key", "Api Key")], string="Auth method")
    th_api_key = fields.Char(string="API Key")
    app = fields.Selection(selection_add=[('curd', 'CURD'), ('partner', 'Partner')], ondelete={"curd": "cascade", "partner": "cascade"})

    def _get_fastapi_routers(self) -> List[APIRouter]:
        # Trả về router đã định tuyến theo trường "app" được cấu hình
        if self.app == 'curd':
            return [curd_router]
        if self.app == 'partner':
            return [partner_router]
        return super()._get_fastapi_routers()

    @api.model
    def _fastapi_app_fields(self) -> List[str]:
        field = super()._fastapi_app_fields()
        # Khi thêm 1 trường mới thì phải thêm ở đây(theo hướng dẫn của fastapi)
        field.append("th_auth_method")
        return field

    def _get_app(self):
        self.clear_caches()
        # check các link website gọi vào API xem có được phép gọi vào api hay không.
        origins = self.th_access_ids.filtered_domain([('th_is_access', '=', True)]).mapped('th_url')
        app = super()._get_app()
        # origins = ['*']
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Kiểm tra lại xem router có sử dụng phương thức bảo mật không (api_key)
        if self.app in ['curd', 'partner']:
            auth_fast_endpoint = (
                th_api_key_based
            )
            app.dependency_overrides[
                fastapi_endpoint_impl
            ] = auth_fast_endpoint
        return app

    # def _prepare_fastapi_app_params(self) -> dict[str, Any]:
    #     params = super()._prepare_fastapi_app_params()
    #     # Trả về hướng dẫn sử dụng api
    #     if self.app == 'curd':
    #         tags_metadata = params.get("openapi_tags", []) or []
    #         tags_metadata.append({"name": "curd", "description": demo_router_doc})
    #         params["openapi_tags"] = tags_metadata
    #
    #     if self.app == 'partner':
    #         tags_metadata = params.get("openapi_tags", []) or []
    #         tags_metadata.append({"name": "partner", "description": demo_router_doc})
    #         params["openapi_tags"] = tags_metadata
    #
    #     return params

    def write(self, vals):
        # cập nhập lại thông tin th_access_ids cho api
        res = super().write(vals)
        if vals.get('th_access_ids', False):
            for rec in self:
                self._get_app()
        return res

    def _get_fastapi_app_dependencies(self) -> List[Depends]:
        """Return the dependencies to use for the fastapi app."""
        # Thêm head chứa lang và api key (trong phần hướng dẫn sử dụng)
        return [Depends(dependencies.accept_language), Depends(dependencies.accept_api_key)]


def th_api_key_based(
        api_key: Annotated[
            str, Depends(APIKeyHeader(name="api-key", description="In this demo, you can use a user's login as api key.")),
        ],
        request: Request,
        env: Annotated[Environment, Depends(odoo_env)],
) -> FastapiEndpoint:
    """
    api key của chính api đang được gọi vào đó
    """
    # Get the first part
    parts = [part for part in request.url.path.split('/') if part]
    first_part = '/' + parts[0] if parts else None

    # Kiểm tra xem api và root path có trên cùng 1 endpoint hay không
    th_api_key = (env["fastapi.endpoint"].sudo().search([("th_api_key", "=", api_key), ('root_path', '=', first_part)], limit=1))
    if not th_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return th_api_key.with_context(th_api_key=api_key)
