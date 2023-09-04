from odoo import models, fields


class University(models.Model):
    _inherit = 'th.university'
    _rec_name = 'name'

    th_university_website_ids = fields.One2many('th.university.web', 'th_university_id')


class WebUniversities(models.Model):
    _name = 'th.university.web'

    name = fields.Char('Website')
    th_state_id = fields.Many2one(comodel_name='res.country.state', required=True, string='State/City', domain="[('country_id.code', '=', 'VN')]")
    th_university_id = fields.Many2one(comodel_name="th.university", string="School")
