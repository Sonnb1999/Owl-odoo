# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
The curd router is a router that demonstrates how to use the fastapi
integration with odoo.
"""
import json
import xmlrpc
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer

from odoo.http import request, Response
from ..schemas import User, ResponseMessage, BackLink
from odoo.addons.base.models.res_partner import Partner
from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import authenticated_partner, fastapi_endpoint, odoo_env, authenticated_fastapi_endpoint
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint as ThFastapi

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(tags=["curd"])


@router.get("/demo")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


@router.get("/users")
def get_partners(fastapi: Annotated[ThFastapi, Depends(authenticated_fastapi_endpoint)]):
    if fastapi:
        # users = request.env['res.users'].sudo().search([])
        users = request.env['res.users'].sudo().search([])
        return [{'name': rec.name, 'display_name': rec.login} for rec in users]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Không có quyền truy cập!"
        )


# limit item
@router.get("/list_item")
async def th_list_item(user_id: int, skip: int = 0, limit: int = 10, token: str = Depends(oauth2_scheme)):
    # list_item = list(range(1, 101))
    return {"token": token}


@router.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


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
                status_code=status.HTTP_400_BAD_REQUEST, detail=str([e, user]),
            )
        if user_create:
            return HTTPException(
                status_code=status.HTTP_200_OK, detail="Đã tạo thành công!"
            )


@router.put("/users/update/{item_id}")
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
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
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
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e),
            )
        return HTTPException(
            status_code=status.HTTP_200_OK, detail="Đã Xoá thành công!"
        )


# @router.get("/check_cookie")
# async def check_cookie(user: Annotated[Partner, Depends(authenticated_partner)]):
#     if user:
#         try:
#             setting = request.env['res.config.settings'].sudo().get_values()
#             th_access_interval_number = setting.get('th_access_interval_number', False)
#             th_access_interval_type = setting.get('th_access_interval_type', False)
#             cookie = {
#                 'th_access_interval_number': th_access_interval_number,
#                 'th_access_interval_type': th_access_interval_type,
#
#             }
#             body = {'results': cookie}
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#         # return cookie
#         return HTTPException(status_code=status.HTTP_200_OK, detail=cookie)
#         # return Response(json.dumps(cookie), status=status.HTTP_200_OK)
#
#
# @router.post("/backlink")
# async def back_link(user: Annotated[Partner, Depends(authenticated_partner)], data: BackLink):
#     if user and data:
#         create_user_click = False
#         try:
#             url = data.link_tracker
#             utm_params = data.odoo_utm_params
#             referrer = data.referrer
#             code = data.code
#
#             utm_source = utm_params.get('utm_source', False)
#             utm_campaign = utm_params.get('utm_campaign', False)
#             utm_medium = utm_params.get('utm_medium', False)
#             if not utm_source:
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT FOUND UTM SOURCE')
#             domain = [('url', '=', url), ('source_id.name', '=', utm_source)]
#
#             if utm_campaign:
#                 domain.append(('campaign_id.name', '=', utm_campaign))
#             else:
#                 domain.append(('campaign_id', '=', utm_campaign))
#
#             if utm_medium:
#                 domain.append(('medium_id.name', '=', utm_medium))
#             else:
#                 domain.append(('medium_id', '=', utm_medium))
#
#             link_tracker = request.env['link.tracker'].sudo().search(domain, limit=1, order='id desc')
#             if not link_tracker:
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT FOUND LINK TRACKER')
#
#             vals = {
#                 'th_count_link_click': int(link_tracker.th_count_link_click) + 1
#             }
#             if not link_tracker.th_count_link_ids or date.today() not in link_tracker.th_count_link_ids.mapped('th_date') \
#                     or referrer not in link_tracker.th_count_link_ids.mapped('th_referrer'):
#                 vals['th_count_link_ids'] = [(0, 0, {
#                     'th_date': date.today(),
#                     'th_click': 1,
#                     'th_referrer': referrer
#                 })]
#             else:
#                 th_count_link_id = link_tracker.th_count_link_ids.search(
#                     [('th_date', '=', date.today()), ('th_referrer', '=', referrer)], limit=1, order='id desc')
#                 th_count_link_id.th_click = th_count_link_id.th_click + 1
#             link_tracker.sudo().write(vals)
#
#             # test data
#             # th_count_link_ids = link_tracker.th_count_link_ids.search([], limit=1, order='id desc')
#             # vals['th_count_link_ids'] = [(0, 0, {
#             #     'th_date': th_count_link_ids.th_date + timedelta(days=1),
#             #     'th_click': th_count_link_ids.th_click + 1,
#             #     'th_referrer': referrer
#             # })]
#             # link_tracker.sudo().write(vals)
#             exist_user = request.env['th.session.user'].sudo().search([('th_user_client_code', '=', code)])
#             if not exist_user:
#                 create_user_click = request.env['th.session.user'].sudo().create({
#                     'th_link_tracker_id': link_tracker.id if link_tracker else False,
#                     'th_website': url,
#                     'th_web_click_ids': [
#                         (0, 0, {
#                             'th_screen_time_start': datetime.now(),
#                             'name': url,
#                         })
#                     ]
#                 })
#             else:
#                 exist_user.write({'th_link_tracker_id': link_tracker.id if link_tracker else False})
#                 web_click_id = request.env['th.web.click'].sudo().search([('th_session_user_id', '=', exist_user.id)],
#                                                                          order="id desc", limit=1)
#                 if web_click_id and web_click_id.name == url:
#                     web_click_id.write({'th_screen_time_end': datetime.now()})
#                 else:
#                     web_click_id.th_screen_time_end = datetime.now()
#                     request.env['th.web.click'].sudo().create({
#                         'th_screen_time_start': datetime.now(),
#                         'name': url,
#                         'th_session_user_id': exist_user.id
#                     })
#
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#
#         try:
#             setting = request.env['res.config.settings'].sudo().get_values()
#             th_access_interval_number = setting.get('th_access_interval_number', False)
#             th_access_interval_type = setting.get('th_access_interval_type', False)
#             cookie = {
#                 'th_access_interval_number': th_access_interval_number,
#                 'th_access_interval_type': th_access_interval_type,
#             }
#         except Exception as e:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
#
#         body = {
#             'code': create_user_click.th_user_client_code if create_user_click else exist_user.th_user_client_code,
#             'cookie': cookie,
#         }
#         return HTTPException(status_code=status.HTTP_200_OK, detail=body)
