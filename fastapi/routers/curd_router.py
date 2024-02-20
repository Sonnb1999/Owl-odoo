# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
The curd router is a router that demonstrates how to use the fastapi
integration with odoo.
"""
import json
import xmlrpc
from typing import Annotated
from odoo.http import request
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
            request.env['res.users'].create({
                'login': data.email,
                'name': data.username
            })
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_200_OK, detail="Đã tạo thành công!"
            )


@router.put("/users/update")
async def update_user(user: Annotated[Partner, Depends(authenticated_partner)], data: User):
    return {"message": "User received"}


@router.delete("/users/delete")
async def update_user(data: User):
    if data:
        raise HTTPException(
            status_code=status.HTTP_200_OK, detail="Delete success!"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=" not found!"
        )
    return {"message": "User received"}
