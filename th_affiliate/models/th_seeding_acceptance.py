from odoo import models, fields, api, _
from datetime import timedelta

from odoo.exceptions import ValidationError

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
    ('is_available', "Available"),
    ('self_writing', "Self writing")
]


class ThAcceptanceSeeding(models.Model):
    _name = 'th.acceptance.seeding'
    _rec_name = 'th_show_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=1, string="Coefficient")
    th_acceptance_type = fields.Selection(selection=acceptance_type_selection_values, string='Type', required=1, default='is_available')
    th_coefficient_convention = fields.Char(string="Coefficient convention")
    th_cost_factor = fields.Float(string='Cost/Factor', tracking=True)
    th_acceptance_cost_history_ids = fields.One2many('th.acceptance.cost.history', 'th_acceptance_seeding_id')
    th_post_link_id = fields.Many2one('th.post.link', 'Post link')
    th_show_name = fields.Char('Show name', compute="_compute_th_show_name", store=True)

    @api.depends('name', 'th_coefficient_convention')
    def _compute_th_show_name(self):
        for rec in self:
            if rec.th_coefficient_convention:
                rec.th_show_name = '%s / %s' % (rec.name, rec.th_coefficient_convention)
            else:
                rec.th_show_name = rec.name

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
                th_acceptance_seeding_old = self.env['th.acceptance.cost.history'].search(
                    [('th_acceptance_seeding_id', '=', rec.id)], limit=1, order='id desc')

                th_start_date = th_acceptance_seeding_old.th_start_date + timedelta(days=1)

                if th_acceptance_seeding_old.th_start_date < fields.Date.today():
                    th_start_date = fields.Date.today() + timedelta(days=1)
                data = {
                    'th_cost_factor': values.get('th_cost_factor'),
                    'th_start_date': th_start_date,
                }
                if th_acceptance_seeding_old.th_start_date == (fields.Date.today() + timedelta(days=1)) and th_acceptance_seeding_old.th_end_date == False:
                    th_acceptance_seeding_old.th_cost_factor = values.get('th_cost_factor')
                else:
                    if not th_acceptance_seeding_old.th_end_date:
                        th_end_date = fields.Date.today()
                        if th_acceptance_seeding_old.th_start_date > fields.Date.today():
                            th_end_date = th_acceptance_seeding_old.th_start_date
                        th_acceptance_seeding_old.write({
                            'th_end_date': th_end_date,
                        })
                    values['th_acceptance_cost_history_ids'] = [(0, 0, data)]
        return super(ThAcceptanceSeeding, self).write(values)


class ThAcceptanceCostHistory(models.Model):
    _name = 'th.acceptance.cost.history'
    _order = 'id desc'

    th_cost_factor = fields.Float(string='Cost/factor', required=True)
    th_start_date = fields.Date(string='Start day', required=True)
    th_end_date = fields.Date(string='End date')
    th_acceptance_seeding_id = fields.Many2one('th.acceptance.seeding', required=1)

    def write(self, values):
        result = super(ThAcceptanceCostHistory, self).write(values)

        for rec in self:
            th_end_date = values.get('th_end_date', False) or rec.th_end_date
            if th_end_date and rec.th_start_date > th_end_date:
                raise ValidationError(_('Time cannot overlap'))
        return result