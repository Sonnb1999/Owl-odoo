from typing import Annotated
from odoo.http import request
from ..schemas import PartnerData, Message
from odoo.api import Environment
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, FastAPI
from ..dependencies import fastapi_endpoint, odoo_env, authenticated_fastapi_endpoint
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint as ThFastapi
from passlib.context import CryptContext
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, EmailStr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import time
app = FastAPI()
router = APIRouter(tags=["partner"])
app.include_router(router)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    username: str | None = None


def write_log(message: Message):
    print(message)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@router.get("/")
async def get_partners(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], background_tasks: BackgroundTasks):
    if fastapi:
        partners = request.env['res.partner'].th_get_partner()
        data_send = [{'name': rec.name, 'display_name': rec.phone} for rec in partners]
        message = {
            'name': 'str',
            'th_url': 'str',
            'th_fastapi_id': fastapi.id,
            'th_data_response': data_send,
            'th_state': 'success',
        }
        background_tasks.add_task(write_log, message)
        return data_send
    else:
        background_tasks.add_task(write_log, "Không có log")
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


@router.get("/{item_id}")
def get_partner(item_id: int, fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)], data: PartnerData):
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
