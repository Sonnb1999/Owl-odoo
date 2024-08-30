from typing import Annotated
from odoo.http import request
from ..schemas import PartnerData
from odoo.api import Environment
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from ..dependencies import fastapi_endpoint, odoo_env, authenticated_fastapi_endpoint
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint as ThFastapi

router = APIRouter(tags=["partner"])


def write_log(message: str):
    print(message)


@router.get("/")
async def get_partners(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], background_tasks: BackgroundTasks):
    if fastapi:
        background_tasks.add_task(write_log, "Starting FastAPI")
        partners = request.env['res.partner'].th_get_partner()
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


@router.post("/{item_id}")
def get_partners(item_id: int, fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
    if fastapi and item_id:
        partners = request.env['res.partner'].th_get_partner(id=item_id)
        return [{'name': rec.name, 'display_name': rec.phone} for rec in partners]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


@router.put("/update/{item_id}")
async def update_user(item_id: int, fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
    if not data.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Vui lòng nhập số điện thoại!')
    if not item_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Không có bản ghi cần chính sửa')

    if fastapi:
        try:
            partners = request.env['res.partner'].th_update_partner(item_id, data.dict())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã chỉnh sửa thành công!"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


@router.delete("/delete/{item_id}")
async def update_user(item_id: int, fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)]):
    if not item_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Không tìm thấy bản ghi!')

    if fastapi:
        try:
            partners = request.env['res.partner'].th_unlink_partner(item_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã xoá thành công!"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )
