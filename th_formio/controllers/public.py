import json
import xmlrpc.client

from odoo import http, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request
from markupsafe import Markup
from urllib.parse import unquote
from odoo.addons.formio.controllers.public import FormioPublicController
from odoo.addons.formio.controllers.utils import (
    generate_uuid4,
    log_form_submisssion,
    update_dict_allowed_keys,
    validate_csrf,
)
import datetime
from odoo.addons.formio.models.formio_builder import STATE_CURRENT as BUILDER_STATE_CURRENT
from odoo.addons.formio.models.formio_form import (
    STATE_DRAFT as FORM_STATE_DRAFT,
    STATE_COMPLETE as FORM_STATE_COMPLETE,
)


class ThFormioPublicController(FormioPublicController):

    @http.route('/formio/public/form/<string:uuid>', type='http', auth='public', website=True)
    def public_form_root(self, uuid):
        form = self._get_public_form(uuid, self._check_public_form())
        if not form:
            msg = 'Form UUID %s' % uuid
            return request.not_found(msg)
        else:
            languages = form.builder_id.languages
            lang_en = request.env.ref('base.lang_en')
            if lang_en.active and form.builder_id.language_en_enable and 'en_US' not in languages.mapped('code'):
                languages |= request.env.ref('base.lang_en')
            values = {
                'form': form,
                'form_languages': languages,
                'formio_css_assets': form.builder_id.formio_css_assets,
                'formio_js_assets': form.builder_id.formio_js_assets,
                'extra_assets': form.builder_id.extra_asset_ids,
                # uuid is used to disable assets (js, css) caching by hrefs
                'uuid': generate_uuid4()
            }
            return request.render('th_formio.th_formio_form_public_embed', values)

    @http.route('/formio/public/form/new/<string:builder_uuid>', type='http', auth='public', methods=['GET'],
                website=True)
    def public_form_new_root(self, builder_uuid):
        """ TODO LEGACY 18.0
        - Remove this endpoint in favor of method (below): public_form_new_current_uuid_root
        - Add to CHANGELOG or UPDATE file: Check the URL of public
          forms and change the UUID to the form.builder current_uuid
          (field)
        """
        formio_builder = self._get_public_builder(builder_uuid)
        if not formio_builder:
            msg = 'Form Builder UUID %s: not found' % builder_uuid
            return request.not_found(msg)
        elif not formio_builder.public:
            msg = 'Form Builder UUID %s: not public' % builder_uuid
            return request.not_found(msg)
        # elif not formio_builder.state != BUILDER_STATE_CURRENT:
        #     msg = 'Form Builder UUID %s not current/published' % builder_uuid
        #     return request.not_found(msg)
        else:
            values = {
                'builder': formio_builder,
                'public_form_new': True,
                # 'languages' already injected in rendering somehow
                'form_languages': formio_builder.languages,
                'formio_css_assets': formio_builder.formio_css_assets,
                'formio_js_assets': formio_builder.formio_js_assets,
                'extra_assets': formio_builder.extra_asset_ids,
                # uuid is used to disable assets (js, css) caching by hrefs
                'uuid': generate_uuid4()
            }
            # Đánh dấu ngày hoạt động khi truy cập vào form mới
            if formio_builder:
                formio_builder.write({'th_action_date': fields.datetime.now()})
            return request.render('th_formio.th_formio_form_public_new_embed', values)

    @http.route('/formio/public/form/new/<string:builder_uuid>/config', type='http', auth='public', methods=['GET'], csrf=False, website=True)
    def public_form_new_config(self, builder_uuid):
        formio_builder = self._get_public_builder(builder_uuid)
        res = {'schema': {}, 'options': {}}

        if not formio_builder or not formio_builder.public or formio_builder.state not in [BUILDER_STATE_CURRENT, 'TEST']:
            return request.make_json_response(res)

        if formio_builder.schema:
            res['schema'] = json.loads(formio_builder.schema)
            res['options'] = self._get_public_new_form_js_options(formio_builder)
            res['locales'] = self._get_public_form_js_locales(formio_builder)
            res['params'] = self._get_public_form_js_params(formio_builder)
            res['csrf_token'] = request.csrf_token()

        args = request.httprequest.args
        etl_odoo_config = formio_builder.sudo()._etl_odoo_config(params=args.to_dict())
        res['options'].update(etl_odoo_config.get('options', {}))

        return request.make_json_response(res)

    @http.route('/formio/public/form/new/<string:builder_uuid>/submit', type='http', auth="public", methods=['POST'], csrf=False, website=True)
    def public_form_new_submit(self, builder_uuid, **kwargs):
        formio_builder = self._get_public_builder(builder_uuid)
        post = request.get_json_data()
        context = {
            'th_ownership_code': formio_builder.th_ownership_unit_id.th_code,
            'th_form_id': formio_builder.uuid,
        }

        th_partner_id = request.env['res.partner']
        th_warehouse_id = request.env['th.origin']
        th_university = False
        company_id = False
        utm_param_source = False
        if not formio_builder or not post:
            # TODO raise or set exception (in JSON resonse) ?
            return

        # Khởi tạo state mặc định
        post['th_state_data'] = 'fake' if formio_builder.th_data_demo else 'real'
        post['th_ownership_unit_id'] = formio_builder.th_ownership_unit_id.id

        # Nếu là demo data, trả về ngay
        if formio_builder.th_data_demo:
            post['th_state_data'] = 'fake'
            return self.create_data_demo(formio_builder, post, {}, context)

        university_form = post['data'].get('university', False)
        major_form = post['data'].get('majors', [])
        utm_url = post['data'].get('th_utm', {})
        description = post['data'].get('th_textArea', '')
        cooperation_program = post['data'].get('cooperation_program', '')
        file = post['data'].get('file', False)
        th_ownership_code = post['data'].get('apm_ownership_unit', False)

        url_parameter = post['data'].get('th_url', '').split('?')
        if len(url_parameter) > 1:
            # giải mã đoạn parameter
            unquote_parameter = unquote(url_parameter[1])
            utm_param_source = unquote_parameter.split('&')[0].split('=')[1]

        if utm_url and utm_url.get('utm_source', False):
            odoo_utm_source = utm_url.get('utm_source', False)
            if odoo_utm_source:
                th_partner_id = request.env['res.partner'].sudo().search([('th_affiliate_code', '=', odoo_utm_source)])
                company_id = th_partner_id.user_ids.company_id.id if th_partner_id else False

        if not th_partner_id:
            th_partner_id = formio_builder.th_ownership_unit_id.th_partner_id
            company_id = formio_builder.th_ownership_unit_id.th_partner_id.user_ids.company_id.id

        values = {
            'th_customer': post['data'].get('name', False),
            'th_email': post['data'].get('email', False),
            'th_phone': str(post['data'].get('phone', '')) and post['data'].get('phone', '').replace(" ", "").replace("\t", ""),
            'th_description': description,
            'th_affiliate_code': th_partner_id.th_affiliate_code,
            'th_utm_source': utm_url.get('utm_source', False) if utm_url.get('utm_source', False) else utm_param_source,
            'th_utm_medium': utm_url.get('utm_medium', False),
            'th_utm_campaign': utm_url.get('utm_campaign', False),
            'th_utm_term': utm_url.get('utm_term', False),
            'th_utm_content': utm_url.get('utm_content', False),
        }
        if cooperation_program:
            values.update({'th_cooperation_program': cooperation_program})

        if post['data'].get('source_group', False):
            values['th_utm_source'] = post['data'].get('source_group', False)
        values['th_channel_id'] = post['data'].get('channel', False)

        # Xử lý logic theo storage location
        try:
            if formio_builder.th_storage_location == 'crm':
                majors = ''
                if isinstance(major_form, list):
                    for major in major_form:
                        if isinstance(major, dict):
                            majors += major.get('name', '') + ', '
                        else:
                            majors += str(major) + ', '
                elif isinstance(major_form, dict):
                    majors = major_form.get('name', '')
                else:
                    # Xử lý khi major_form là chuỗi hoặc kiểu dữ liệu khác
                    majors = str(major_form)
                if university_form:
                    th_university = university_form.get('name', False)
                    th_warehouse_id = request.env['th.origin'].search(
                        [('th_code', '=', university_form.get('university_code', ' ko có code'))], limit=1)

                str_university = '\n\n' + "Trường: " + str(th_university) if th_university else ''
                str_major = '\n\n' + "Ngành: " + majors if majors else ''
                description += str_university + str_major
                major_code_university = major_form.get('major_code_university')

                # values['th_source_name'] = 'Form nhúng'
                values['th_description'] = description
                values['th_warehouse_code'] = th_warehouse_id.th_code if th_warehouse_id else False
                values['th_form_name'] = formio_builder.title
                values['th_uuid_form'] = builder_uuid
                values['th_major_code_university'] = major_code_university

                try:
                    server_api = request.env['th.api.server'].search([('state', '=', 'deploy'), ('th_type', '=', 'samp')], limit=1, order='id desc')
                    if not server_api:
                        raise ValidationError('Lỗi hệ thống do không tìm thấy server!')

                    result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_api.th_url_api), allow_none=True)
                    db = server_api.th_db_api
                    uid_api = server_api.th_uid_api
                    password = server_api.th_password
                    context['aff_crm_lead_form'] = True
                    values = self._sanitize_and_encode(values)
                    filtered_context = self._sanitize_and_encode(context)
                    result_apis.execute_kw(db, uid_api, password, 'crm.lead', 'create_lead_aff', [[], values], {'context': filtered_context})
                    post['th_sambala_pushed'] = True

                except Exception as e:
                    print(e)
                    post['th_state_data'] = 'real'
                    post['th_ownership_unit_id'] = formio_builder.th_ownership_unit_id
                    post['th_error_form'] = str(e)
                    return self.create_data_demo(formio_builder, post)

            elif formio_builder.th_storage_location == 'prm':
                server_api = request.env['th.api.server'].search([('state', '=', 'deploy'), ('th_type', '=', 'samp')], limit=1, order='id desc')
                if not server_api:
                    raise ValidationError('Lỗi hệ thống do không tìm thấy server!')

                result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_api.th_url_api), allow_none = True)
                db = server_api.th_db_api
                uid_api = server_api.th_uid_api
                password = server_api.th_password
                context['aff_prm_lead'] = True
                
                domain = []
                if values.get('th_mail'):
                    domain.append(['th_partner_email', '=', values['th_mail']])

                if values.get('th_phone'):
                    domain.append(['th_partner_phone', '=', values['th_phone']])

                if formio_builder.th_ownership_unit_id.th_code:
                    domain.append(['th_ownership_unit_id.th_code', '=', formio_builder.th_ownership_unit_id.th_code])

                if domain:
                    exist_lead = result_apis.execute_kw(db, uid_api, password, 'prm.lead', 'search', [domain], {'context': context})
                    if exist_lead:
                        values['exist_lead_id'] = exist_lead[0]
                        result_apis.execute_kw(db, uid_api, password, 'prm.lead', 'th_send_mail_duplicate', [[], values], {'context': context})
                    else:
                        # Xử lý các giá trị None trước khi gửi
                        values = self._sanitize_and_encode(values)
                        filtered_context = self._sanitize_and_encode(context)
                        result_apis.execute_kw(db, uid_api, password, 'prm.lead', 'create_lead_aff', [[], values], {'context': filtered_context})
                post['th_sambala_pushed'] = True

            elif formio_builder.th_storage_location == 'apm':
                if th_ownership_code:
                    context['th_ownership_code'] = th_ownership_code.get('th_code', False) if th_ownership_code.get('th_code', False) else context['th_ownership_code']
                values['th_warehouse_code'] = formio_builder.th_origin_id.th_code
                
                server_api = request.env['th.api.server'].search([('state', '=', 'deploy'), ('th_type', '=', 'samp')], limit=1, order='id desc')
                if not server_api:
                    raise ValidationError('Lỗi hệ thống do không tìm thấy server!')

                result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_api.th_url_api), allow_none = True)
                db = server_api.th_db_api
                uid_api = server_api.th_uid_api
                password = server_api.th_password
                context['aff_apm_lead'] = True
                values = self._sanitize_and_encode(values)
                filtered_context = self._sanitize_and_encode(context)
                result_apis.execute_kw(db, uid_api, password, 'th.apm', 'create_lead_aff', [[], values], {'context': filtered_context})
                post['th_sambala_pushed'] = True

        except Exception as e:
            print(e)
            post['th_error_form'] = str(e)

        return self.create_data_demo(formio_builder, post, values, context)

    def create_data_demo(self, formio_builder, post, values, context):
        Form = request.env['formio.form']
        description = Markup('')
        for rec in post['data']:
            if rec == 'th_url':
                description += Markup('<strong>Website</strong>: <strong>%s</strong><br>') % (post['data'][rec])
            elif rec == 'th_utm':
                description += Markup('<strong>UTM website</strong>: <strong>%s</strong><br>') % (post['data'][rec])
            elif rec == 'submit':
                continue
            else:
                description += Markup('<strong>%s</strong>: <strong>%s</strong><br>') % (_(rec), post['data'][rec])
        vals = {
            'builder_id': formio_builder.id,
            'title': formio_builder.title,
            'public_create': True,
            'public_share': True,
            'submission_data': json.dumps(post['data']),
            'th_submission_data': description,
            'submission_date': fields.Datetime.now(),
            'submission_user_id': request.env.user.id,
            'th_state_data': post['th_state_data'],
            'th_error_form': post.get('th_error_form', False),
            'th_sambala_value': json.dumps(values),
            'th_sambala_context': json.dumps(context), 
            'th_sambala_pushed': post.get('th_sambala_pushed', False),
        }

        save_draft = post.get('saveDraft') or (post['data'].get('saveDraft') and not post['data'].get('submit'))

        if save_draft:
            vals['state'] = FORM_STATE_DRAFT
        else:
            vals['state'] = FORM_STATE_COMPLETE

        context = {'tracking_disable': True}

        # Create form only once
        if request.env.user._is_public():
            Form = Form.with_company(request.env.user.sudo().company_id)
            form = Form.with_context(**context).sudo().create(vals)
        else:
            form = Form.with_context(**context).create(vals)
            
        if vals.get('state') == FORM_STATE_COMPLETE:
            form.after_submit()

        request.session['formio_last_form_uuid'] = form.uuid
        res = {
            'form_uuid': form.uuid,
            'submission_data': form.submission_data
        }
        return request.make_json_response(res)

    def _sanitize_values(self, values, default_empty=''):
        """
        Xử lý các giá trị None trong dictionary, thay thế bằng giá trị mặc định
        @param values: Dictionary cần xử lý
        @param default_empty: Giá trị mặc định thay thế cho None
        @return: Dictionary đã được xử lý
        """
        if not values:
            return {}
        
        sanitized = {}
        for key, value in values.items():
            if value is None:
                sanitized[key] = default_empty
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_values(value, default_empty)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_values(item, default_empty) if isinstance(item, dict) 
                    else (default_empty if item is None else item)
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_and_encode(self, data):
        """Xử lý dữ liệu và chuyển qua JSON để đảm bảo không có None"""
        sanitized = self._sanitize_values(data, '')
        return json.loads(json.dumps(sanitized))