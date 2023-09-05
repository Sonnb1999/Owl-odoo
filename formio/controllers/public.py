# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import json
import logging

from markupsafe import Markup

from odoo import http, fields, _
from odoo.http import request

from ..models.formio_builder import \
    STATE_CURRENT as BUILDER_STATE_CURRENT

from ..models.formio_form import \
    STATE_PENDING as FORM_STATE_PENDING, STATE_DRAFT as FORM_STATE_DRAFT, \
    STATE_COMPLETE as FORM_STATE_COMPLETE, STATE_CANCEL as FORM_STATE_CANCEL

_logger = logging.getLogger(__name__)


class FormioPublicController(http.Controller):

    ####################
    # Form - public uuid
    ####################

    @http.route('/formio/public/form/<string:uuid>', type='http', auth='public', website=True)
    def public_form_root(self, uuid, **kwargs):
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
                'extra_assets': form.builder_id.extra_asset_ids
            }
            return request.render('formio.formio_form_public_embed', values)

    @http.route('/formio/public/form/<string:form_uuid>/config', type='json', auth='public', website=True)
    def form_config(self, form_uuid, **kwargs):
        form = self._get_public_form(form_uuid, self._check_public_form())
        res = {'schema': {}, 'options': {}, 'params': {}}

        if form and form.builder_id.schema:
            res['schema'] = json.loads(form.builder_id.schema)
            res['options'] = self._get_public_form_js_options(form)
            res['locales'] = self._get_public_form_js_locales(form.builder_id)
            res['params'] = self._get_public_form_js_params(form.builder_id)

        args = request.httprequest.args
        etl_odoo_config = form.builder_id.sudo()._etl_odoo_config(params=args.to_dict())
        res['options'].update(etl_odoo_config.get('options', {}))
        return res

    @http.route('/formio/public/form/<string:uuid>/submission', type='json', auth='public', website=True)
    def public_form_submission(self, uuid, **kwargs):
        form = self._get_public_form(uuid, self._check_public_form())

        # Submission data
        if form and form.submission_data:
            submission_data = json.loads(form.submission_data)
        else:
            submission_data = {}

        # ETL Odoo data
        if form:
            etl_odoo_data = form.sudo()._etl_odoo_data()
            submission_data.update(etl_odoo_data)

        return json.dumps(submission_data)

    @http.route('/formio/public/form/<string:uuid>/submit', type='json', auth="public", methods=['POST'], website=True)
    def public_form_submit(self, uuid, **post):
        """ POST with ID instead of uuid, to get the model object right away """

        form = self._get_public_form(uuid, self._check_public_form())
        if not form:
            # TODO raise or set exception (in JSON resonse) ?
            return

        vals = {
            'submission_data': json.dumps(post['data']),
            'submission_user_id': request.env.user.id,
            'submission_date': fields.Datetime.now(),
        }

        if post.get('saveDraft') or (post['data'].get('saveDraft') and not post['data'].get('submit')):
            vals['state'] = FORM_STATE_DRAFT
        else:
            vals['state'] = FORM_STATE_COMPLETE

        form.write(vals)

        if vals.get('state') == FORM_STATE_COMPLETE:
            form.after_submit()

    ###################
    # Form - public new
    ###################

    @http.route('/formio/public/form/new/<string:builder_uuid>', type='http', auth='public', methods=['GET'], website=True)
    def public_form_new_root(self, builder_uuid, **kwargs):
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
                'extra_assets': formio_builder.extra_asset_ids
            }
            return request.render('formio.formio_form_public_new_embed', values)

    @http.route('/formio/public/form/new/<string:builder_uuid>/config', type='json', auth='public', website=True)
    def public_form_new_config(self, builder_uuid, **kwargs):
        formio_builder = self._get_public_builder(builder_uuid)
        res = {'schema': {}, 'options': {}}

        # if not formio_builder or not formio_builder.public or formio_builder.state != BUILDER_STATE_CURRENT:
        if not formio_builder or not formio_builder.public:
            return res

        if formio_builder.state == BUILDER_STATE_CURRENT or formio_builder.state == 'TEST':
            if formio_builder.schema:
                res['schema'] = json.loads(formio_builder.schema)
                res['options'] = self._get_public_new_form_js_options(formio_builder)
                res['locales'] = self._get_public_form_js_locales(formio_builder)
                res['params'] = self._get_public_form_js_params(formio_builder)

            args = request.httprequest.args
            etl_odoo_config = formio_builder.sudo()._etl_odoo_config(params=args.to_dict())
            res['options'].update(etl_odoo_config.get('options', {}))

            return res

    @http.route('/formio/public/form/new/<string:builder_uuid>/submission', type='json', auth='public', website=True)
    def public_form_new_submission(self, builder_uuid, **kwargs):
        formio_builder = self._get_public_builder(builder_uuid)

        if not formio_builder or not formio_builder.public:
            _logger.info('formio.builder with UUID %s not found' % builder_uuid)
            # TODO raise or set exception (in JSON resonse) ?
            return

        args = request.httprequest.args
        submission_data = {}
        etl_odoo_data = formio_builder.sudo()._etl_odoo_data(params=args.to_dict())
        submission_data.update(etl_odoo_data)
        return json.dumps(submission_data)

    @http.route('/formio/public/form/new/<string:builder_uuid>/submit', type='json', auth="public", methods=['POST'], website=True)
    def public_form_new_submit(self, builder_uuid, **post):
        formio_builder = self._get_public_builder(builder_uuid)
        aff_cook_partner_id = False
        if not formio_builder:
            # TODO raise or set exception (in JSON resonse) ?
            return

        if formio_builder.th_data_demo:
            return self.create_data_demo(formio_builder, post)

        name = post['data'].get('name', '')
        email = post['data'].get('email', '')
        phone = post['data'].get('phone', '')
        another_infor = post['data'].get('info', '')
        url = post['data'].get('th_url', '')
        university_form = post['data'].get('university', False)
        major_form = post['data'].get('majors', False)
        utm_url = post['data'].get('th_utm', False)

        if utm_url and utm_url.get('utm_source', False):
            odoo_utm_source = utm_url.get('utm_source', False)
            aff_cook_partner_id = request.env['res.partner'].sudo().search(
                [('th_affiliate_code', '=', odoo_utm_source)]).id
        affiliate = aff_cook_partner_id

        if not affiliate and url:
            affiliate_school = request.env['th.university.web'].search([('name', 'like', url)], limit=1, order='id desc').mapped('th_university_id')
            if affiliate_school.th_partner_id:
                affiliate = affiliate_school.th_partner_id.th_affiliate_code

        campaign_id = ''
        if utm_url and utm_url.get('utm_campaign', False):
            odoo_utm_campaign = utm_url.get('utm_campaign', False)
            campaign_id = request.env['utm.campaign'].sudo().search([('title', '=', odoo_utm_campaign)]).id

        partner_id = self.th_create_contact(phone, email, name, url)
        if formio_builder.th_storage_location == 'crm':
            if partner_id:
                if university_form:
                    university_code = post['data']['university']['university_code']
                    th_university_form = request.env['th.university'].sudo().search([('th_code', '=', university_code)])

                majors = []
                if major_form:
                    for major in major_form:
                        if major:

                            majors_code = major.get('major_code_aum', False)
                            majors_name = major.get('name', False)
                            if major.get('major_code_aum', False):
                                major_id = request.env['th.major'].sudo().search(
                                    [('th_major_code_aum', '=', majors_code)]).id
                            else:
                                major_id = request.env['th.major'].sudo().search([('name', '=', majors_name)]).id
                            if major_id:
                                majors.append(major_id)

                th_university = request.env['th.university'].search([('th_code', '=', 'AUM')], limit=1)

                university = th_university_form.id if university_form else th_university.id
                create_crm_values = {
                    'partner_id': partner_id,
                    'description': another_infor,
                    'th_partner_referred_id': affiliate,
                    'th_university_id': university,
                    'th_major_ids': majors,
                    'type': 'opportunity',
                    'campaign_id': campaign_id,
                }
                request.env['crm.lead'].sudo().with_context(web_form=True).create(create_crm_values)
        elif formio_builder.th_storage_location == 'prm':
            create_pom_values = {
                'th_partner_id': partner_id,
            }
            request.env['prm.lead'].sudo().with_context(web_form=True).create(create_pom_values)
        elif formio_builder.th_storage_location == 'vmc':
            create_vmc_values = {
                'th_partner_id': partner_id,
            }
            request.env['th.trm.lead'].sudo().with_context(web_form=True).create(create_vmc_values)

    def th_create_contact(self, phone, email, name, url):
        partner_id = False
        if phone != '' or email != '':
            check_contact = request.env['res.partner'].sudo().search([('phone', '=', phone)])
            check_contact.sudo().write({
                'phone': check_contact.phone if check_contact.phone else phone,
                'email': check_contact.email if check_contact.email else email,
            })

            if check_contact:
                partner_id = check_contact.id
            else:
                partner_id = request.env['res.partner'].sudo().create({
                    'name': name, 'email': email,
                    'phone': phone, 'website': url,
                }).id
        return partner_id

    def create_data_demo(self, formio_builder, post):
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
            'submission_user_id': request.env.user.id
        }

        save_draft = post.get('saveDraft') or (post['data'].get('saveDraft') and not post['data'].get('submit'))

        if save_draft:
            vals['state'] = FORM_STATE_DRAFT
        else:
            vals['state'] = FORM_STATE_COMPLETE

        context = {'tracking_disable': True}

        if request.env.user._is_public():
            Form = Form.with_company(request.env.user.sudo().company_id)
            res = Form.with_context(**context).sudo().create(vals)
        else:
            res = Form.with_context(**context).create(vals)
        if vals.get('state') == FORM_STATE_COMPLETE:
            res.after_submit()
        request.session['formio_last_form_uuid'] = res.uuid
        return {'form_uuid': res.uuid}

    #########
    # Helpers
    #########
    def _get_public_form_js_options(self, form):
        options = form._get_js_options()

        Lang = request.env['res.lang']
        # language
        if request.context.get('lang'):
            options['language'] = Lang._formio_ietf_code(request.context.get('lang'))
        elif request.env.user.lang:
            options['language'] = Lang._formio_ietf_code(request.env.user.lang)
        else:
            options['language'] = request.env.ref('base.lang_en').formio_ietf_code
        options['i18n'] = form.i18n_translations()
        return options

    def _get_public_new_form_js_options(self, builder):
        options = {
            'public_create': True,
            'embedded': True,
            'i18n': builder.i18n_translations()
        }

        # language
        Lang = request.env['res.lang']
        if request.context.get('lang'):
            options['language'] = Lang._formio_ietf_code(request.context.get('lang'))
        elif request.env.user.lang:
            options['language'] = Lang._formio_ietf_code(request.env.user.lang)
        else:
            options['language'] = request.env.ref('base.lang_en').formio_ietf_code

        return options

    def _get_public_form_js_locales(self, builder):
        return builder._get_form_js_locales()

    def _get_public_form_js_params(self, builder):
        return builder._get_public_form_js_params()

    def _get_public_form(self, form_uuid, public_share=False):
        return request.env['formio.form'].get_public_form(form_uuid, public_share)

    def _get_public_builder(self, builder_uuid):
        return request.env['formio.builder'].get_public_builder(builder_uuid)

    def _check_public_form(self):
        return request.env.uid == request.env.ref('base.public_user').id or request.env.uid

    def _get_form(self, uuid, mode):
        return request.env['formio.form'].get_form(uuid, mode)
