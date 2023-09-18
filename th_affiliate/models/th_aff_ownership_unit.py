from odoo import models, fields, api


class AffOwnershipUnit(models.Model):
    _name = 'th.aff.ownership.unit'
    _rec_name = 'name'

    name = fields.Char('Đơn vị sở hữu', required=1)
    th_code_aff = fields.Char('Mã đơn vị sở hữu')
    th_member_ids = fields.Many2many(comodel_name='res.users', relation='th_aff_ownership_res_user', column1="th_aff_ownership_id", column2='th_res_id', string='Người dùng')

