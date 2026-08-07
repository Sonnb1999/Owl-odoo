import json
import logging

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager

_logger = logging.getLogger(__name__)
ORIGIN = ['th_setup_parameters.th_aum_university_origin', 'th_setup_parameters.th_origin_vmc', 'th_setup_parameters.th_origin_vstep',]


class ThCustomController(CustomerPortal):

    @http.route('/get_universities', type='http', auth="none", csrf=False)
    def university(self, **kwargs):
        universities = request.env['th.origin'].sudo().search([('id', 'not in', [request.env.ref(origin).id for origin in ORIGIN])])
        data = []
        for rec in universities:
            data.append({'name': rec.name, 'university_code': rec.th_code})
        return json.dumps(data)

    @http.route('/get_majors', type='http', auth="none", csrf=False)
    def major(self, **kwargs):
        if 'university' in kwargs:
            majors = request.env['th.origin'].sudo().search([('th_code', '=', kwargs['university'])]).mapped(
                'th_university_major_ids')
        else:
            majors = request.env['th.major'].sudo().search([('name', '!=', 'AUM')])
        data = []
        for rec in majors:
            if rec.th_major_code_university:
                data.append({'name': rec.th_major_id.name, 'major_code_university': rec.th_major_code_university})
            else:
                data.append({'name': rec.th_major_id.name, 'major_code_university': rec.th_major_code_university})
        return json.dumps(data)

    @http.route('/get_ownership_units', type='http', auth="none", csrf=False)
    def ownership_unit(self, **kwargs):
        ownership_units = request.env['th.ownership.unit'].sudo().search([('name', '!=', 'AUM')])
        data = []
        for rec in ownership_units:
            data.append({'name': rec.name, 'id': rec.id})

        return json.dumps(data)

    @http.route('/get_apm_ownership_units', type='http', auth="none", csrf=False)
    def apm_ownership_unit(self, **kwargs):
        ownership_units = request.env['th.ownership.unit'].sudo().search([])
        data = []
        for rec in ownership_units:
            data.append({'name': rec.name, 'th_code': rec.th_code})

        return json.dumps(data)
    @http.route('/get_apm_product_line', type='http', auth="none", csrf=False)
    def apm_product_line(self, **kwargs):
        ownership_units = request.env.ref('th_setup_parameters.th_origin_vmc')
        ownership_units |= request.env.ref('th_setup_parameters.th_origin_vstep')
        data = []
        for rec in ownership_units:
            data.append({'name': rec.name, 'id': rec.id})

        return json.dumps(data)
