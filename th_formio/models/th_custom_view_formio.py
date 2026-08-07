from odoo import models, fields


class ThCustomViewFormio(models.Model):

    _name = 'th.custom.view.formio'
    _description = 'ẩn cấu hình view form (phần js)'

    th_key = fields.Char('Tên trường', required=1)
    th_value = fields.Char('key', required=1)
    state = fields.Boolean('Trạng thái', default=True)
