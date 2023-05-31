
import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_round
from datetime import datetime


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _domain_leave_manager_id(self):
        user_ids = self.env['res.users'].search([]).filtered(lambda u: u.has_group('hr_holidays.group_hr_holidays_user') or u.has_group('hr_holidays.group_hr_holidays_manager'))
        return [('id', 'in', user_ids.ids)]

    leave_manager_id = fields.Many2one(
        'res.users', domain=_domain_leave_manager_id)

    def _compute_allocation_count(self):
        starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)
        ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)

        data = self.env['hr.leave.allocation'].read_group([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.active', '=', True),
            ('state', '=', 'validate'),
            ('date_from', '>=', starting_day_of_current_year),
            ('date_to', '<=', ending_day_of_current_year),
        ], ['number_of_days:sum', 'employee_id'], ['employee_id'])
        rg_results = dict(
            (d['employee_id'][0], {"employee_id_count": d['employee_id_count'], "number_of_days": d['number_of_days']})
            for d in data)
        for employee in self:
            result = rg_results.get(employee.id)
            employee.allocation_count = float_round(result['number_of_days'], precision_digits=2) if result else 0.0
            employee.allocation_display = "%g" % employee.allocation_count
            employee.allocations_count = result['employee_id_count'] if result else 0.0

    def _get_remaining_leaves(self):
        """ Helper to compute the remaining leaves for the current employees
            :returns dict where the key is the employee id, and the value is the remain leaves
        """
        self._cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                (
                    SELECT holiday_status_id, number_of_days,
                        state, employee_id
                    FROM hr_leave_allocation
                    WHERE date_from >= date_trunc('year', now()) and date_to <= (date_trunc('year', now()+ interval '1 year') - interval '1 day')
                    UNION ALL
                    SELECT holiday_status_id, (number_of_days * -1) as number_of_days,
                        state, employee_id
                    FROM hr_leave
                ) h
                join hr_leave_type s ON (s.id=h.holiday_status_id)
            WHERE
                s.active = true AND h.state='validate' AND
                s.requires_allocation='yes' AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(self.ids),))
        return dict((row['employee_id'], row['days']) for row in self._cr.dictfetchall())