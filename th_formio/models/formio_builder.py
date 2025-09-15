import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
STATE_DRAFT = 'DRAFT'
STATE_TEST = 'TEST'
STATE_IMPLEMENTATION_REQUEST = 'IMPLEMENTATION_REQUEST'
STATE_CURRENT = 'CURRENT'
STATE_OBSOLETE = 'OBSOLETE'

READONLY_STATES = {
    STATE_IMPLEMENTATION_REQUEST: [('readonly', True)],
    STATE_CURRENT: [('readonly', True)],
    STATE_OBSOLETE: [('readonly', True)],
}

STATES = [('TEST', "Test"),  (STATE_IMPLEMENTATION_REQUEST, "Implementation request"),  (STATE_CURRENT, "Deploy")]


class Builder(models.Model):
    _inherit = 'formio.builder'

    name = fields.Char(copy = False)
    th_storage_location = fields.Selection(selection=[('apm', 'APM'), ('crm', 'CRM'), ('prm', 'PRM')], string="Kho cơ hội", states=READONLY_STATES)
    th_public_url = fields.Char(string='Public URL', compute='_compute_public_url')
    th_own_url = fields.Many2one('th.link.form', string='own URL')
    th_set_cookie = fields.Char(string='Set cookie', compute='_compute_public_url')
    th_data_demo = fields.Boolean(string='Create data demo', default=False, compute='compute_change_state', store=True)
    th_ownership_unit_id = fields.Many2one('th.ownership.unit', string='Đơn vị sở hữu', states=READONLY_STATES)
    th_state_care = fields.Selection(selection=[('keep', 'Đối tác tự chăm'), ('transfer', 'Tư vấn chăm')], string="Kiểu chăm", states=READONLY_STATES, default=False)
    th_origin_id = fields.Many2one(comodel_name='th.origin', string="Dòng sản phẩm", domain=[('th_module_ids.name', '=', 'APM')])
    state = fields.Selection(selection_add=STATES, ondelete={STATE_TEST: "cascade", STATE_IMPLEMENTATION_REQUEST: "cascade"})
    th_domain_own = fields.Char(compute="_compute_th_domain_own", default='[]')
    th_action_date = fields.Date(string="Ngày hoạt động")
    @api.depends('formio_version_id')
    def _compute_th_domain_own(self):
        for rec in self:
            domain = []
            th_ownership_id = self.env['th.ownership.unit'].search([]).filtered(
                lambda l: self.env.uid in l.th_user_ids.ids)
            if th_ownership_id:
                domain.append(('id', 'in', th_ownership_id.ids))
            else:
                domain.append(('id', 'in', []))
            rec.th_domain_own = json.dumps(domain)

    def action_preview_form(self):
        return {
            'name': _("Preview form"),
            'type': 'ir.actions.act_url',
            'url': self.th_public_url,
            'target': 'new',
        }

    @api.depends('state')
    def compute_change_state(self):
        for rec in self:
            if rec.state == STATE_TEST:
                rec.th_data_demo = True
            if rec.state == STATE_CURRENT:
                rec.th_data_demo = False

    # def action_request_impl(self):
    #     self.ensure_one()
    #     th_form_manager_ids = self.env['ir.config_parameter'].sudo().get_param('th_form_manager_ids')
    #     users = self.env['res.users'].sudo().search([('id', 'in', eval(th_form_manager_ids) if th_form_manager_ids else [])])
    #     if users:
    #         self.write({'state': STATE_IMPLEMENTATION_REQUEST})
    #         for user in users:
    #             self.message_post(
    #                 body=_('Bạn có 1 yêu cần duyệt form nhúng'),
    #                 partner_ids=user.partner_id.ids)
    #     else:
    #         raise ValidationError('Hiện tại không có người duyệt form vui lòng liên hệ với quản trị hệ thống!')

    @api.depends('public')
    def _compute_public_url(self):
        res = super()._compute_public_url()
        try:
            for rec in self:
                if rec.public and request:
                    url_root = request.httprequest.url_root
                    self.public_url = '%s%s/%s' % (url_root, 'formio/public/form/new', rec.uuid)
                    # thêm: th_set_cookie,th_public_url và chỉnh sửa public_url

                    formio_url = '%s%s/%s/' % (url_root, 'formio/public/form/new', rec.uuid)
                    rec.th_public_url = '%s%s/%s/' % (url_root, 'formio/public/form/new', rec.uuid)

                    rec.public_url = \
                        '<div id="formio_form_iframe_container_%s" class="formio_form_iframe_container"></div >' \
                        '<script src = "%sth_formio/static/src/js/get_utm_url.js"></script>' \
                        '<script>GetForm("%s", "%s") </script>' \
                        '<script src = "%sformio/static/lib/iframe-resizer/iframeResizer.min.js"></script>' \
                        "<script> iFrameResize({heightCalculationMethod: 'grow', }, '.formio_form_embed'); </script>" \
                        % (rec.uuid, url_root, formio_url, rec.uuid, url_root)

                    rec.th_set_cookie = '<script src = "%sformio/static/src/js/set_cookie.js" ></script>' % url_root

                else:
                    rec.public_url = False
                    rec.th_public_url = False
                    rec.th_set_cookie = False
        except Exception as e:
            print(e)

    @api.onchange('th_storage_location')
    def onchange_th_storage_location(self):
        pass
        # for rec in self:
        #     if rec.th_storage_location != 'crm':
        #         rec.th_state_care = False

    def action_draft(self):
        vals = {'state': STATE_DRAFT}
        for rec in self:
            if rec.is_locked:
                vals['is_locked'] = False
            rec.write(vals)

    def action_test(self):
        for rec in self:
            vals = {'state': STATE_TEST, 'public': True}
            if rec.is_locked:
                vals['is_locked'] = False
            rec.write(vals)

    def action_current(self):
        self.ensure_one()
        self.write({'state': STATE_CURRENT, 'is_locked': True, 'public': True})

    @api.model
    def get_public_builder(self, uuid):
        """ Verifies public (e.g. website) access to forms and return builder or False. """

        domain = [
            ('uuid', '=', uuid),
            ('public', '=', True),
        ]
        builder = self.sudo().search(domain, limit=1)
        if builder:
            return builder
        else:
            return False

    @api.model
    def create(self, values):
        if not values.get('name', False):
            values['name'] = self._default_uuid()
        result = super(Builder, self).create(values)
        return result


