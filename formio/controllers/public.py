# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import json
import logging

from odoo import http, fields
from odoo.http import request

from ..models.formio_builder import \
    STATE_CURRENT as BUILDER_STATE_CURRENT

from ..models.formio_form import \
    STATE_PENDING as FORM_STATE_PENDING, STATE_DRAFT as FORM_STATE_DRAFT, \
    STATE_COMPLETE as FORM_STATE_COMPLETE, STATE_CANCEL as FORM_STATE_CANCEL

_logger = logging.getLogger(__name__)


class FormioPublicController(http.Controller):

    ###############
    # Form - public
    ###############

    @http.route('/formio/public/form/<string:uuid>', type='http', auth='public', website=True)
    def public_form_root(self, uuid, **kwargs):
        form = self._get_public_form(uuid, self._check_public_form())
        if not form:
            msg = 'Form UUID %s' % uuid
            return request.not_found(msg)
        else:
            values = {
                'form': form,
                # 'languages' already injected in rendering somehow
                'form_languages': form.builder_id.languages,
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
            res['locales'] = self._get_public_form_js_locales(form)
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

        if not formio_builder or not formio_builder.public or formio_builder.state != BUILDER_STATE_CURRENT:
            return res

        if formio_builder.schema:
            res['schema'] = json.loads(formio_builder.schema)
            res['options'] = self._get_public_new_form_js_options(formio_builder)
            res['locales'] = self._get_public_form_js_locales(formio_builder)
            res['params'] = self._get_public_form_js_params(formio_builder)

        args = request.httprequest.args
        etl_odoo_config = formio_builder.sudo()._etl_odoo_config(params=args.to_dict())
        res['options'].update(etl_odoo_config.get('options', {}))

        return res

    @http.route('/formio/public/form/new/<string:builder_uuid>/submit', type='json', auth="public", methods=['POST'], website=True)
    def public_form_new_submit(self, builder_uuid, **post):
        formio_builder = self._get_public_builder(builder_uuid)
        if not formio_builder:
            # TODO raise or set exception (in JSON resonse) ?
            return

        name = ''
        email = ''
        phone = ''
        another_infor = ''
        # lead_id = False
        th_source = ''
        duplicate = ''

        if 'name' in post['data']:
            name = post['data']['name']

        if 'email' in post['data']:
            email = post['data']['email']

        if 'phone' in post['data']:
            phone = post['data']['phone']

        if 'info' in post['data']:
            another_infor = post['data']['info']

        if 'th_source' in post['data']:
            th_source = post['data']['th_source']

        if name != '' and (phone != '' or email != ''):
            check_contact = request.env['res.partner'].sudo().search(['|', ('email', '=', email), ('phone', '=', phone)])

            if check_contact:
                duplicate = 'Trùng contact'

            check_contact.sudo().write({'comment': duplicate})

            partner_id = request.env['res.partner'].sudo().create(
                {'name': name,
                 'email': email,
                 'phone': phone,
                 'comment': duplicate,
                 }).id

            request.env['crm.lead'].sudo().create({
                'name': name,
                'partner_id': partner_id,
                'description': another_infor + th_source,
                'type': 'opportunity',
            })

    #########
    # Helpers
    #########

    def _get_public_form_js_options(self, form):
        options = form._get_js_options()

        Lang = request.env['res.lang']
        language = Lang._formio_ietf_code(request.env.user.lang)
        if language:
            options['language'] = language
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
