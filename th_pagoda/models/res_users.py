from odoo import fields, models


class Users(models.Model):
    _inherit = 'res.users'

    pg_check_click = fields.Float('click')
