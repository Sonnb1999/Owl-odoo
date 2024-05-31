from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Attachment(models.Model):
    _name = 'th.attachment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Attachment for Application Forms'

    name = fields.Char('Tên file', required=True, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='File đính kèm', required=True, tracking=True, copy=False)

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
