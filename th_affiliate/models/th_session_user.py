import uuid
from odoo import models, fields, api, _


class ThSessionUser(models.Model):
    _name = "th.session.user"
    _rec_name = 'name'

    name = fields.Char("Tên")
    th_user_client_code = fields.Char(default=lambda self: self._default_uuid(), required=True, readonly=True, copy=False, string='Mã code người dùng')
    th_link_tracker_id = fields.Many2one('link.tracker')
    th_web_click_ids = fields.One2many('th.web.click', 'th_session_user_id')
    th_referrer_link = fields.Char('')
    th_website = fields.Char('Tên website')

    @api.model
    def _default_uuid(self):
        return str(uuid.uuid4())

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('customer.visitor.name')
        return super(ThSessionUser, self).create(values)


class ThWebClick(models.Model):
    _name = "th.web.click"
    name = fields.Char('Tên website')
    th_session_user_id = fields.Many2one('th.session.user')
    th_screen_time_start = fields.Datetime('start')
    th_screen_time_end = fields.Datetime('end')
    th_total_time = fields.Char('Tổng giờ')
