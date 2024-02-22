from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    th_potential_customers = fields.Boolean('Khách hàng tiềm năng')
