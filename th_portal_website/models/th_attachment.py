from odoo import models, fields, api
from odoo.exceptions import ValidationError
READONLY_STATES = {
    'accept': [('readonly', True)],
    'reject': [('readonly', True)],
}

class Attachment(models.Model):
    _name = 'th.attachment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Attachment for Application Forms'

    name = fields.Char('Tên file', required=True, tracking=True, states=READONLY_STATES)
    attachment_ids = fields.Many2many('ir.attachment', string='File đính kèm', required=True, tracking=True, copy=False, states=READONLY_STATES)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'chờ duyệt'), ('accept', 'Chấp thuận'), ('reject', 'Từ chối')], default="draft", tracking=True,)
    th_type = fields.Selection([('application_forms', 'Biểu mẫu'), ('regulations', 'Quy định')], string='loại văn bản', states=READONLY_STATES)

    @api.model
    def create(self, values):
        res = super(Attachment, self).create(values)
        for rec in res:
            if len(rec.attachment_ids) > 1:
                raise ValidationError('1 Đơn không thể có 2 file')
        return res

    def write(self, values):
        res = super(Attachment, self).write(values)
        for rec in self:
            if len(rec.attachment_ids) > 1:
                raise ValidationError('1 Đơn không thể có 2 file')
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
