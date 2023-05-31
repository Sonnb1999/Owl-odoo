from odoo import models, fields, _, api, exceptions


class HrLeaveAccrualPlan(models.Model):
    _inherit = 'hr.leave.accrual.plan'

    th_days_add = fields.Float('Days add')
    th_period = fields.Selection([('day', 'Days'), ('hour', 'Hours')], string='Period')
    th_frequency = fields.Selection([('day', 'Day'),
                                     ('month', 'Month'),
                                     ('year', 'Year')], string='Frequency', required=1)
    th_max_days = fields.Float('Maximum days')
    th_unused_days = fields.Selection([('postponed', 'Transferred to the next year'), ('lost', 'Monetize')], string="At the end of the calendar year, unused accruals will be", default='lost', required='True')
    th_period_number = fields.Float('Number of period', default=1.0)

    @api.onchange('time_off_type_id')
    def _onchange_time_off_type_id(self):
        if self.time_off_type_id:
            self.th_period = self.time_off_type_id.request_unit if self.time_off_type_id.request_unit == 'hour' else 'day'

    @api.constrains('th_days_add', 'th_max_days', 'th_period_number')
    def _check_th_days_add_and_max_days(self):
        for rec in self:
            if self.th_period_number and 0 > self.th_period_number:
                raise exceptions.ValidationError(_("Frequency must be greater than 0."))
            if self.th_max_days and 0 > self.th_max_days:
                raise exceptions.ValidationError(_("Maximum times must be greater than 0."))
            if self.th_days_add and 0 > self.th_days_add:
                raise exceptions.ValidationError(_("Times must be greater than 0."))
            if rec.th_days_add and rec.th_max_days and rec.th_days_add > rec.th_max_days:
                raise exceptions.ValidationError(_('Time cannot be greater than maximum time'))