from odoo import models, fields


class ThTranslates(models.Model):

    _name = 'th.translate'
    _description = 'dịch thuật'

    lang_id = fields.Many2one('res.lang', 'Ngôn ngữ')
    th_key = fields.Char('Từ khóa')
    th_value = fields.Char('Dịch')
