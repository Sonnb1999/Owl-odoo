from odoo import models, fields


class University(models.Model):
    _name = 'th.university'
    _rec_name = 'name'

    name = fields.Char('University name')
    th_url = fields.Char('For University website')
    th_code = fields.Char('University code')
