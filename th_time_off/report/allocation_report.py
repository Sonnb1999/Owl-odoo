import datetime
import json
from odoo import api, fields, models, Command, _
# from odoo.exceptions import UserError, ValidationError
# from odoo.tools.float_utils import float_round
# from odoo.tools.misc import format_date
# import datetime
from dateutil.relativedelta import relativedelta


class Allocation(models.AbstractModel):
    _name = 'allocation.report'
    _description = 'Allocation report'

    def get_header(self, options):
        return [
            [
                {'name': _('Employee'),
                 'style': 'width: 250px; border-radius: 3% 0 0 0; background: #A9E2F3; text-align:center; height: 50px;'},
                {'name': _('Time of type'),
                 'style': 'width: 250px; border: none; background: #A9E2F3; text-align:center;'},
                {'name': _('Implementation date'),
                 'style': 'width: 200px; border: none; background: #A9E2F3; text-align:center;'},
                {'name': _('Allocation duration'),
                 'style': 'width: 200px; border: none; background: #A9E2F3; text-align:center;'},
                {'name': _('Available days'),
                 'style': 'width: 200px; border: none; background: #A9E2F3; text-align:center;border-radius: 0 3% 0 0;'},
            ],
        ]

    def get_lines(self, year):
        data = self._do_query(year)
        for line in data:

            if line['request_unit'] == 'day' or line['request_unit'] == 'half_day':
                if line['th_leaves_taken']:
                    the_remaining_days = line['number_of_days'] - line['th_leaves_taken']
                else:
                    the_remaining_days = line['number_of_days']
                line['the_remaining_days'] = the_remaining_days

            else:

                number_of_hours_display = line['th_number_of_hours_display']
                the_remaining_hours = line['th_number_of_hours_display'] - line['th_leaves_taken'] * \
                                      8 if line['th_leaves_taken'] else line['th_number_of_hours_display']

                line['the_remaining_days'] = the_remaining_hours
        return data
        return result_lines

    def _do_query(self, year):
        query = self._get_query(year)
        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return result

    def _get_query(self, year):
        date_from = datetime.date.today().replace(day=1, month=1, year=year)
        date_to = datetime.date.today().replace(day=31, month=12, year=year)
        return f'''
                select he.name as employee_name,hlt.name as leave_type_name,hla.date_from,
                hla.date_to, hla.th_duration_display,hla.th_leaves_taken,hla.th_max_leaves,
                hla.th_number_of_hours_display,hlt.request_unit,hla.number_of_days,hla.id,he.id as employee_id

                from hr_leave_allocation hla
                join hr_employee he on he.id = hla.employee_id
                join hr_leave_type hlt on hlt.id = hla.holiday_status_id
                where hlt.th_check_type = 'is_paid_leave' and hla.state = 'validate' and hla.date_from BETWEEN '{date_from}'
                and '{date_to}' and hla.date_to BETWEEN '{date_from}' and '{date_to}'
                group by he.id, hlt.id, hla.id
        '''

    def get_report_customs(self, data):
            report = self.env.ref('th_time_off.action_report_th_allocation')
            return report.report_action(self.env['hr.leave.allocation'].browse(28), data)
