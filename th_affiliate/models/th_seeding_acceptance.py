from odoo import models, fields, api
from datetime import timedelta

# coefficient_selection_values = [
#     ('CN1', "CN1"),
#     ('GR1', "GR1"),
#     ('GR2', "GR2"),
#     ('GR3', "GR3"),
#     ('CN2', "CN2"),
#     ('GR4', "GR4"),
#     ('GR5', "GR5"),
#     ('GR6', "GR6")
# ]

acceptance_type_selection_values = [
    ('is_available', "Có sẵn"),
    ('self_writing', "Tự viết")
]


class ThAcceptanceSeeding(models.Model):
    _name = 'th.acceptance.seeding'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # name = fields.Char("Tên")
    name = fields.Char(required=1, string="Hệ số")
    th_acceptance_type = fields.Selection(selection=acceptance_type_selection_values, string='Loại', required=1, default='is_available')
    th_coefficient_convention = fields.Char(string="Quy ước hệ số")
    th_cost_factor = fields.Float(string='Chi phí/hệ số', tracking=True)
    th_acceptance_cost_history_ids = fields.One2many('th.acceptance.cost.history', 'th_acceptance_seeding_id')
    th_post_link_id = fields.Many2one('th.post.link', 'Post link')


    @api.model
    def create(self, values):
        if values.get('th_cost_factor', False):
            data = {
                'th_cost_factor': values.get('th_cost_factor'),
                'th_start_date': fields.Date.today(),
                # 'th_end_date': values.get('create_date'),

            }
            values['th_acceptance_cost_history_ids'] = [(0, 0, data)]
        return super(ThAcceptanceSeeding, self).create(values)

    def write(self, values):
        th_cost_factor = values.get('th_cost_factor', False)
        for rec in self:
            if th_cost_factor:
                th_acceptance_seeding_old_id = self.env['th.acceptance.cost.history'].search(
                    [('th_acceptance_seeding_id', '=', rec.id)], limit=1, order='id desc')
                th_acceptance_seeding_old_id.write({
                    'th_end_date': fields.Date.today(),
                })
                data = {
                    'th_cost_factor': values.get('th_cost_factor'),
                    'th_start_date': fields.Date.today(),
                    # 'th_end_date': values.get('create_date'),

                }
                values['th_acceptance_cost_history_ids'] = [(0, 0, data)]
        return super(ThAcceptanceSeeding, self).write(values)


class ThAcceptanceCostHistory(models.Model):
    _name = 'th.acceptance.cost.history'
    _order = 'id desc'

    th_cost_factor = fields.Float(string='Chi phí/hệ số')
    th_start_date = fields.Date(string='Ngày bắt đầu')
    th_end_date = fields.Date(string='Ngày Kết thúc')
    th_acceptance_seeding_id = fields.Many2one('th.acceptance.seeding')
