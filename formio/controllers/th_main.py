import json
import logging

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager

_logger = logging.getLogger(__name__)


class ThCustomController(CustomerPortal):

    @http.route('/get_universities', type='http', auth="none", csrf=False)
    def university(self, **kwargs):
        universities = request.env['th.university'].sudo().search([])
        data = []
        for rec in universities:
            data.append({'name': rec.name, 'university_code': rec.th_code})
        return json.dumps(data)

    @http.route('/get_majors', type='http', auth="none", csrf=False)
    def major(self, **kwargs):
        if 'university' in kwargs:
            majors = request.env['th.university'].sudo().search([('th_code', '=', kwargs['university'])]).mapped(
                'th_university_major_ids.th_major_id')
        else:
            majors = request.env['th.major'].sudo().search([])
        data = []
        for rec in majors:
            if rec.th_major_code_aum:
                data.append({'name': rec.name, 'major_code_aum': rec.th_major_code_aum})
            else:
                data.append({'name': rec.name, 'major_code_aum': rec.th_major_code_aum})
        return json.dumps(data)
