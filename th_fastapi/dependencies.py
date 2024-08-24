# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from typing import TYPE_CHECKING, Annotated

from odoo.api import Environment
from odoo.exceptions import AccessDenied

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from odoo.addons.fastapi.context import odoo_env_ctx
from .schemas import Paging

from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint as ThFastapi


def company_id() -> int | None:
    """This method may be overriden by the FastAPI app to set the allowed company
    in the Odoo env of the endpoint. By default, the company defined on the
    endpoint record is used.
    """
    return None


def odoo_env(company_id: Annotated[int | None, Depends(company_id)]) -> Environment:
    env = odoo_env_ctx.get()
    if company_id is not None:
        env = env(context=dict(env.context, allowed_company_ids=[company_id]))

    yield env


def authenticated_partner_impl() -> Partner:
    """This method has to be overriden when you create your fastapi app
    to declare the way your partner will be provided. In some case, this
    partner will come from the authentication mechanism (ex jwt token) in other cases
    it could comme from a lookup on an email received into an HTTP header ...
    See the fastapi_endpoint_demo for an example"""


def authenticated_partner_env(partner: Annotated[Partner, Depends(authenticated_partner_impl)]) -> Environment:
    """Return an environment with the authenticated partner id in the context"""
    return partner.with_context(authenticated_partner_id=partner.id).env


def authenticated_partner(
    partner: Annotated[Partner, Depends(authenticated_partner_impl)],
    partner_env: Annotated[Environment, Depends(authenticated_partner_env)],
) -> Partner:
    """If you need to get access to the authenticated partner into your
    endpoint, you can add a dependency into the endpoint definition on this
    method.
    This method is a safe way to declare a dependency without requiring a
    specific implementation. It depends on `authenticated_partner_impl`. The
    concrete implementation of authenticated_partner_impl has to be provided
    when the FastAPI app is created.
    This method return a partner into the authenticated_partner_env
    """
    return partner_env["res.partner"].browse(partner.id)


# Gọi vào fastapi
def fastapi_endpoint_impl() -> ThFastapi:
    """This method has to be overriden when you create your fastapi app
       to declare the way your partner will be provided. In some case, this
       partner will come from the authentication mechanism (ex jwt token) in other cases
       it could comme from a lookup on an email received into an HTTP header ...
       See the fastapi_endpoint_demo for an example"""


def authenticated_fastapi_env(fastapi: Annotated[ThFastapi, Depends(fastapi_endpoint_impl)]) -> Environment:
    """Return an environment with the authenticated partner id in the context"""
    return fastapi.with_context(authenticated_partner_id=fastapi.id).env


# sử dụng cho router
def authenticated_fastapi_endpoint(fastapi: Annotated[ThFastapi, Depends(fastapi_endpoint_impl)],
                                   fastapi_env: Annotated[Environment, Depends(authenticated_fastapi_env)]) -> ThFastapi:
    return fastapi_env["fastapi.endpoint"].browse(fastapi.id)



def paging(
    page: Annotated[int, Query(gte=1)] = 1, page_size: Annotated[int, Query(gte=1)] = 80
) -> Paging:
    """Return a Paging object from the page and page_size parameters"""
    return Paging(limit=page_size, offset=(page - 1) * page_size)


def basic_auth_user(
    credential: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Users:
    username = credential.username
    password = credential.password
    try:
        uid = (
            env["res.users"]
            .sudo()
            .authenticate(
                db=env.cr.dbname, login=username, password=password, user_agent_env=None
            )
        )
        return env["res.users"].browse(uid)
    except AccessDenied as ad:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        ) from ad


def authenticated_partner_from_basic_auth_user(
    user: Annotated[Users, Depends(basic_auth_user)],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Partner:
    return env["res.partner"].browse(user.sudo().partner_id.id)


def fastapi_endpoint_id() -> int:
    """This method is overriden by the FastAPI app to make the fastapi.endpoint record
    available for your endpoint method. To get the fastapi.endpoint record
    in your method, you just need to add a dependency on the fastapi_endpoint method
    defined below
    """


def fastapi_endpoint(
    _id: Annotated[int, Depends(fastapi_endpoint_id)],
    env: Annotated[Environment, Depends(odoo_env)],
) -> "FastapiEndpoint":
    """Return the fastapi.endpoint record"""
    return env["fastapi.endpoint"].browse(_id)


def accept_language(
    accept_language: Annotated[
        str | None,
        Header(
            alias="Accept-Language",
            description="The Accept-Language header is used to specify the language "
            "of the content to be returned. If a language is not available, the "
                        "server will return the content in the default language.",
        ),
    ] = None,
) -> str:
    """This dependency is used at application level to document the way the language
    to use for the response is specified. The header is processed outside of the
    fastapi app to initialize the odoo environment with the right language.
    """
    return accept_language


def accept_api_key(
        accept_api_key: Annotated[
            str | None,
            Header(
                alias="api-key",
                description="The Accept-Language header is used to specify the key ",
            ),
        ] = None,
) -> str:
    """This dependency is used at application level to document the way the language
    to use for the response is specified. The header is processed outside of the
    fastapi app to initialize the odoo environment with the right language.
    """
    return accept_api_key


def accept_api_auth(
        accept_api_key: Annotated[
            str | None,
            Header(
                alias="api-key",
                description="The Accept-Language header is used to specify the key ",
            ),
        ] = None,
) -> str:
    """This dependency is used at application level to document the way the language
    to use for the response is specified. The header is processed outside of the
    fastapi app to initialize the odoo environment with the right language.
    """
    return accept_api_key
