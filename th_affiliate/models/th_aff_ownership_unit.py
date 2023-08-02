from odoo import models, fields, api


class AffOwnershipUnit(models.Model):
    _name = 'th.aff.ownership.unit'
    _rec_name = 'name'

    name = fields.Char("Đơn vị sở hữu")
    th_code_aff = fields.Char("Mã đơn vị sở hữu")
