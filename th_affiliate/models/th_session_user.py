import uuid
from odoo import models, fields, api


class ThSessionUser(models.Model):
    _name = "th.session.user"

    th_user_client_code = fields.Char(default=lambda self: self._default_uuid(), required=True, readonly=True, copy=False, string='Mã code người dùng')
    th_link_tracker_id = fields.Many2one('link.tracker')
    th_web_click_ids = fields.One2many('th.web.click', 'th_session_user_id')

    @api.model
    def _default_uuid(self):
        return str(uuid.uuid4())


class ThWebClick(models.Model):
    _name = "th.web.click"
    name = fields.Char()
    th_session_user_id = fields.Many2one('th.session.user')
    th_screen_time_start = fields.Datetime('start')
    th_screen_time_end = fields.Datetime('end')
    th_total_time = fields.Char('Tổng giờ')
