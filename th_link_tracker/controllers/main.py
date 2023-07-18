# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import time

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request, Response
from odoo.addons.link_tracker.controller.main import LinkTracker


class ThLinkTracker(LinkTracker):
    pass
    # @http.route('/r/<string:code>', type='http', auth='public', website=True)
    # def full_url_redirect(self, code, **post):
    #     if not request.env['ir.http'].is_a_bot():
    #         country_code = request.geoip.get('country_code')
    #         request.env['link.tracker.click'].sudo().add_click(
    #             code,
    #             ip=request.httprequest.remote_addr,
    #             country_code=country_code,
    #         )
    #     redirect_url = request.env['link.tracker'].get_url_from_code(code)
    #     if not redirect_url:
    #         raise NotFound()
    #     request.future_response.set_cookie('odoo_utm_source', 'utm_source_in_th_link', max_age=60000, httponly=True)
    #     return request.redirect(redirect_url, code=301, local=False)
    #
    # @http.route('/get/back',  type='json', auth='none', csrf=False, cors='*')
    # def get_back(self, **post):
    #
    #     exist_client = request.env['th.link.tracker.back'].search([('th_ip_client', '=', post['ip_client'])])
    #
    #     if exist_client:
    #         exist_client.write({
    #             'th_full_url': post['full_url'],
    #             'th_country': post['country'],
    #             'th_utm': post['utm'],
    #             'th_url': post['url'],
    #         })
    #         return {
    #             "Message": "edit Success"
    #         }
    #
    #     create_value = {
    #         'th_full_url': post['full_url'],
    #         'th_ip_client': post['ip_client'],
    #         'th_country': post['country'],
    #         'th_utm': post['utm'],
    #         'th_url': post['url'],
    #     }
    #
    #     request.env['th.link.tracker.back'].create(create_value)
    #     return {
    #         "Message": "Success"
    #     }
