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

from ..dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    odoo_env, accept_api_key, fastapi_endpoint_impl
)
from ..routers import curd_router, demo_router_doc
from fastapi.middleware.cors import CORSMiddleware
from .. import dependencies


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    th_access_ids = fields.One2many('th.access.url', 'th_fastapi_id')

    app = fields.Selection(
        selection_add=[("demo", "Demo Endpoint"), ('partner', 'Partner'), ('curd', 'CURD')],
        ondelete={"demo": "cascade", "partner": "cascade", "curd": "cascade"}
    )
    demo_auth_method = fields.Selection(
        selection=[("api_key", "Api Key"), ("http_basic", "HTTP Basic")],
        string="Authenciation method",
    )
    th_api_key_id = fields.Char(string="API Key ID")

    def _get_fastapi_routers(self) -> List[APIRouter]:
        # Trả về router đã định tuyến theo thẻ trường app được cấu hình
        super()._get_fastapi_routers()
        if self.app == 'curd':
            return [curd_router]
        return super()._get_fastapi_routers()

    @api.constrains("app", "demo_auth_method")
    def _validate_demo_auth_method(self):
        for rec in self:
            if rec.app in ['curd', 'demo', 'partner'] and not rec.demo_auth_method:
                raise ValidationError(
                    _(
                        "The authentication method is required for app %(app)s",
                        app=rec.app,
                    )
                )

    @api.model
    def _fastapi_app_fields(self) -> List[str]:
        fields = super()._fastapi_app_fields()
        fields.append("demo_auth_method")
        return fields

    def _get_app(self):
        self.clear_caches()
        # check xem trang web đấy có được gọi vào api này không
        origins = self.th_access_ids.filtered_domain([('th_is_access', '=', True)]).mapped('th_url')
        app = super()._get_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Kiểm tra lại xem router có sử dụng các phương thức bảo mật không (http_basic or api_key)
        if self.app in ['curd']:
            if self.demo_auth_method == "http_basic":
                auth_fast_endpoint = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                auth_fast_endpoint = (
                    th_api_key_based
                )
            app.dependency_overrides[
                fastapi_endpoint_impl
            ] = auth_fast_endpoint
        return app

    def _prepare_fastapi_app_params(self) -> dict[str, Any]:
        params = super()._prepare_fastapi_app_params()

        # Trả về hướng dẫn sử dụng api của từng router
        if self.app == 'curd':
            tags_metadata = params.get("openapi_tags", []) or []
            tags_metadata.append({"name": "curd", "description": demo_router_doc})
            params["openapi_tags"] = tags_metadata

        return params

    def write(self, vals):
        res = super().write(vals)
        if vals.get('th_access_ids', False):
            for rec in self:
                self._get_app()
        return res

    def _get_fastapi_app_dependencies(self) -> List[Depends]:
        """Return the dependencies to use for the fastapi app."""
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
    print(first_part)
    th_api_key = (env["fastapi.endpoint"].sudo().search([("th_api_key_id", "=", api_key), ('root_path', '=', first_part)], limit=1))
    if not th_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return th_api_key.with_context(th_api_key_id=api_key)
