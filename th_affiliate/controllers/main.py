# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import time

from werkzeug.exceptions import NotFound

from odoo import http, api
from odoo.http import request, Response
from odoo.addons.link_tracker.controller.main import LinkTracker
import json


class ThLinkTracker(LinkTracker):
    @http.route('/api/check_cookie', type='http', auth='none')
    def check_cookie(self, **kwargs):
        setting = request.env['res.config.settings'].sudo().get_values()
        th_access_interval_number = setting.get('th_access_interval_number', False)
        th_access_interval_type = setting.get('th_access_interval_type', False)

        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, Content-Type, Access-Control-Allow-Origin"
        }
        cookie = {
            'th_access_interval_number': th_access_interval_number,
            'th_access_interval_type': th_access_interval_type,

        }
        body = {'results': cookie}
        return Response(json.dumps(body), headers=headers)

    @http.route('/api/backlink', type='json', auth='none', cors='*', csrf=False)
    def get_back_1(self, **post):
        exist_client = request.env['link.tracker.click'].sudo().search([])
        body = {"Message": "Success"}
        return body

    @http.route('/get/back', type='json', auth='none', csrf=False, cors='*')
    def get_back(self, **post):

        exist_client = request.env['link.tracker'].search([])

        return {
            "Message": "Success"
        }

    # @http.route('/api/backlink', type='json', auth='none', csrf=False, cors='*')
    # def get_back_2(self, **post):
    #     exist_client = request.env['link.tracker'].search([])
    #
    #     return {
    #         "Message": "Success"
    #     }
