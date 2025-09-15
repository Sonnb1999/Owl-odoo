from odoo import models, fields


class ThOwnershipUnit(models.Model):
    _inherit = "th.ownership.unit"
    _description = "Đơn vị sở hữu"

    name = fields.Char(string="Tên sở hữu", required=True)
    th_description = fields.Text(string="Mô tả")
    th_partner_id = fields.Many2one(comodel_name="res.partner", string="Tên liên hệ")
    th_partner_website_ids = fields.One2many('th.partner.web', 'th_ownership_unit_id')


class WebUniversities(models.Model):
    _name = 'th.partner.web'
    _description = "Trang web của đại lý"

    name = fields.Char('Website')
    th_state_id = fields.Many2one(comodel_name='res.country.state', required=True, string='State/City', domain="[('country_id.code', '=', 'VN')]")
    th_ownership_unit_id = fields.Many2one(comodel_name="th.ownership.unit", string="Partner")
