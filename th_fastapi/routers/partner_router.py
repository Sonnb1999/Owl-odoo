# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
from typing import Annotated
from odoo.http import request
from ..schemas import PartnerData
from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import authenticated_partner, fastapi_endpoint, odoo_env, authenticated_fastapi_endpoint
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint as ThFastapi

router = APIRouter(tags=["curd"])


@router.get("/partners")
def get_partners(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)]):
    if fastapi:
        partners = request.env['res.partner'].th_get_partner(datas=None)
        return [{'name': rec.name, 'display_name': rec.phone} for rec in partners]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


@router.post("/create")
def get_partners(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
    if fastapi:
        partners = request.env['res.partner'].th_create_partner(datas=data.dict())
        return [{'name': rec.name, 'display_name': rec.phone} for rec in partners]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


@router.put("/update")
async def update_user(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
    if not data.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Vui lòng nhập số điện thoại!')

    if fastapi:
        try:
            partners = request.env['res.partner'].th_update_partner(datas=data.dict())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã chỉnh sửa thành công!"
        )


@router.delete("/delete")
async def update_user(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
    if not data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Không tìm thấy bản ghi!')

    if fastapi:
        try:
            partners = request.env['res.partner'].th_unlink_partner(datas=data.dict())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã xoá thành công!"
        )
