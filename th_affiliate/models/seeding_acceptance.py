from odoo import models, fields, api

coefficient_selection_values = [
    ('CN1', "CN1"),
    ('GR1', "GR1"),
    ('GR2', "GR2"),
    ('GR3', "GR3"),
    ('CN2', "CN2"),
    ('GR4', "GR4"),
    ('GR5', "GR5"),
    ('GR6', "GR6")
]

acceptance_type_selection_values = [
    ('is_available', "Có sẵn"),
    ('self_writing', "Tự viết")
]


class SeedingCategory(models.Model):
    _name = 'th.acceptance.seeding'
    _rec_name = 'th_coefficient'

    # name = fields.Char("Tên")
    th_acceptance_type = fields.Selection(selection=acceptance_type_selection_values, string='Loại', required=1, default='is_available')
    th_coefficient = fields.Selection(selection=coefficient_selection_values, required=1, string="Hệ số")
    th_coefficient_convention = fields.Char(string="Quy ước hệ số")
    th_cost_factor = fields.Float(string='Chi phí/hệ số')
