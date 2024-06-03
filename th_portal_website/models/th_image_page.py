from odoo import models, fields, api
from odoo.exceptions import ValidationError
READONLY_STATES = {
    'accept': [('readonly', True)],
    'reject': [('readonly', True)],
}


class ThImagePage(models.Model):
    _name = 'th.image.page'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Attachment for Application Forms'

    name = fields.Char('Tên ảnh', required=True, tracking=True, states=READONLY_STATES)
    th_url = fields.Char(string='Link ảnh', required=True, tracking=True, states=READONLY_STATES)
    th_description = fields.Text(string='Mô tả', tracking=True, states=READONLY_STATES)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'chờ duyệt'), ('accept', 'Chấp thuận'), ('reject', 'Từ chối')], default="draft", tracking=True,)

    @api.model
    def create(self, values):
        res = super(ThImagePage, self).create(values)
        for rec in res:
            pass
            # if len(rec.attachment_ids) > 1:
            #     raise ValidationError('1 Đơn không thể có 2 file')
        return res

    def write(self, values):
        res = super(ThImagePage, self).write(values)
        for rec in self:
            pass
            # if len(rec.attachment_ids) > 1:
            #     raise ValidationError('1 Đơn không thể có 2 file')
        return res

    def th_action_accept(self):
        for rec in self:
            rec.state = 'accept'

    def th_action_reject(self):
        for rec in self:
            rec.state = 'reject'

    def th_action_draft(self):
        for rec in self:
            rec.state = 'draft'
