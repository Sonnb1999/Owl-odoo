# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import json
import logging
import xmlrpc
from datetime import datetime
from odoo import http, fields
from odoo.http import request, Response
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
_logger = logging.getLogger(__name__)


class StudentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'get_student_info' in counters:
            domain = []
            # values['get_student_info'] = (str(request.env['th.student.info'].sudo().search_count(domain)))
            values['get_student_info'] = (str(1))

        if 'get_major' in counters:
            domain = []
            values['get_student_info'] = (str(1))

        return values

    # link seeding
    @http.route(['/my/student'], type='http', auth="user", website=True)
    def student_info(self, **kwargs):
        values = {
            'page_name': 'student_info',
        }

        return request.render("th_portal_student.th_student", values)

    @http.route(['/my/get_student_info', '/my/get_student_info/page/<int:page>'], type='http', auth="user", website=True)
    def list_get_link_seeding(self, page=1, sortby='id', search='', search_in="All", **kwargs):
        student_code = request.env.user.partner_id.th_student_code
        school_code = request.env.user.partner_id.th_student_code
        th_api = request.env['th.api.server'].search([('state', '=', 'deploy'), ('th_type', '=', 'samp')], limit=1, order='id desc')
        try:
            result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(th_api.th_url_api))
        except Exception as e:
            print(e)
        db = th_api.th_db_api
        uid_api = th_api.th_uid_api
        password = th_api.th_password
        orders = result_apis.execute_kw(db, uid_api, password, 'th.student', 'search_read', [[['th_student_code', '=', student_code]]], {'limit': 1})
        data = {}
        if orders:
            data = {
                'student_code': student_code,
                'name': orders[0].get('th_student_name'),
                'birthday': orders[0].get('th_partner_birthday'),
                'major': orders[0].get('th_major_id')[1],
                'phone': orders[0].get('th_partner_phone'),
                'email': orders[0].get('th_partner_email'),
                'acceptance': orders[0].get('th_acceptance'),
                'gender': orders[0].get('th_acceptance') if orders[0].get('th_acceptance') else 'Nam',
                'place_of_birth': orders[0].get('th_acceptance') if orders[0].get('th_acceptance') else "Viết Nam",
            }

        values = {
            'data': data,
            'page_name': 'get_student_info',
            # 'form_exist': form_exist
        }
        return request.render("th_portal_student.th_list_get_student_info", values)

    @http.route(['/my/major_student', '/my/major_student/page/<int:page>'], type='http', auth="user", website=True)
    def th_object_student(self, page=1, sortby='id', search='', search_in="All", **kwargs):
        domain = []
        th_link_tracker = request.env['th.student.info']
        total_links = th_link_tracker.sudo().search_count(domain)
        page_detail = pager(url='/my/get_link',
                            total=total_links,
                            page=page,
                            step=10)
        link_seeds = th_link_tracker.sudo().search(domain, limit=10, offset=page_detail['offset'], order='id desc')
        values = {
            'students': link_seeds,
            'page_name': 'own_links',
            'pager': page_detail,
        }
        return request.render("th_portal_student.th_list_object", values)
