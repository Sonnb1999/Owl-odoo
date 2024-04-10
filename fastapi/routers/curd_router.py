# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
The curd router is a router that demonstrates how to use the fastapi
integration with odoo.
"""
import json
import xmlrpc
from typing import Annotated
from odoo.http import request, Response
from odoo.api import Environment
from odoo.models import BaseModel
from odoo.addons.base.models.res_partner import Partner
from fastapi import APIRouter, Depends, HTTPException, status
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError

from ..models import FastapiEndpoint
from ..dependencies import authenticated_partner, fastapi_endpoint, odoo_env
from ..schemas import User, ResponseMessage

router = APIRouter(tags=["curd"])


@router.get("/demo")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


@router.get("/users")
def get_partners(user: Annotated[Partner, Depends(authenticated_partner)]):
    if user:
        users = request.env['res.users'].sudo().search([])
        return [{'name': rec.name, 'display_name': rec.login} for rec in users]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


@router.post("/users/create")
async def create_user(user: Annotated[Partner, Depends(authenticated_partner)], data: User):
    if user:
        try:
            user_create = request.env['res.users'].create({
                'login': data.email,
                'name': data.username
            })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=e,
            )
        if user_create:
            return HTTPException(
                status_code=status.HTTP_200_OK, detail="Đã tạo thành công!"
            )


@router.put("/users/update")
async def update_user(user: Annotated[Partner, Depends(authenticated_partner)], data: User):
    if not data.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Vui lòng nhập email!')

    if user:
        try:
            user_id = request.env['res.users'].sudo().search([('login', '=', data.email)], limit=1, order='id DESC')
            if user_id:
                user_id.write({
                    'login': data.email,
                    'name': data.username if data.username else user_id
                })
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=e,
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã chỉnh sửa thành công!"
        )


@router.delete("/users/delete")
async def unlink_user(user: Annotated[Partner, Depends(authenticated_partner)], data: User):
    if user:
        try:
            user_id = request.env['res.users'].sudo().search([('login', '=', data.email)], limit=1, order='id DESC')
            if user_id:
                user_id.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=e,
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã Xoá thành công!"
        )


@router.get("/check_cookie")
async def check_cookie(user: Annotated[Partner, Depends(authenticated_partner)]):
    if user:
        try:
            setting = request.env['res.config.settings'].sudo().get_values()
            th_access_interval_number = setting.get('th_access_interval_number', False)
            th_access_interval_type = setting.get('th_access_interval_type', False)
            cookie = {
                'th_access_interval_number': th_access_interval_number,
                'th_access_interval_type': th_access_interval_type,

            }
            body = {'results': cookie}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)
        # return cookie
        return HTTPException(status_code=status.HTTP_200_OK, detail=cookie)
        # return Response(json.dumps(cookie), status=status.HTTP_200_OK)
