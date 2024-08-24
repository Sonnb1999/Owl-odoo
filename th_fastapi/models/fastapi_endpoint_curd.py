# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
from typing import Annotated, Any, List

from a2wsgi import ASGIMiddleware

from odoo import _, api, fields, models, tools
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, HTTPException, status, FastAPI
from fastapi.security import APIKeyHeader

from ..dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    odoo_env, accept_api_key
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
                authenticated_partner_impl_override = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                authenticated_partner_impl_override = (
                    th_api_key_based
                )
            app.dependency_overrides[
                authenticated_partner_impl
            ] = authenticated_partner_impl_override
        return app

    def _prepare_fastapi_app_params(self) -> dict[str, Any]:
        params = super()._prepare_fastapi_app_params()

        # Trả về hướng dẫn sử dụng api của từng router
        if self.app in ['demo', 'partner']:
            tags_metadata = params.get("openapi_tags", []) or []
            tags_metadata.append({"name": "demo", "description": demo_router_doc})
            params["openapi_tags"] = tags_metadata

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


def api_key_based_authenticated_partner_impl(
        api_key: Annotated[
            str,
            Depends(
                APIKeyHeader(
                    name="api-key",
                    description="In this demo, you can use a user's login as api key.",
                )
            ),
        ],
        env: Annotated[Environment, Depends(odoo_env)],
) -> Partner:
    """A dummy implementation that look for a user with the same login
    as the provided api key
    """
    partner = (
        env["res.users"].sudo().search([("login", "=", api_key)], limit=1).partner_id
    )
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return partner


def th_api_key_based(
        api_key: Annotated[
            str,
            Depends(
                APIKeyHeader(
                    name="api-key",
                    description="In this demo, you can use a user's login as api key.",
                )
            ),
        ],
        env: Annotated[Environment, Depends(odoo_env)],
) -> FastapiEndpoint:
    """A dummy implementation that look for a user with the same login
    as the provided api key
    """
    th_api_key = (env["fastapi.endpoint"].sudo().search([("th_api_key_id", "=", api_key)], limit=1))
    if not th_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return th_api_key
