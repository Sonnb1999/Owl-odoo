from collections import defaultdict
from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from lxml import etree
from dateutil.relativedelta import relativedelta
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo import api, fields, models, tools, SUPERUSER_ID

class th_hrLeaveType(models.Model):
    _inherit = 'hr.leave'

    state = fields.Selection(selection_add=[('validate1',)], tracking=False)
    th_reason_refuse = fields.Text('Reason')
    th_allocation_number_of_days = fields.Float(string="The number of days allocated", compute="_compute_th_allocation_number_of_days")
    th_remaining_number_of_days = fields.Float(string="Remaining day(s)", compute="_compute_th_remaining_number_of_days")
    th_used_time_off = fields.Many2many('th.used.time.off', string='Leave', compute="_compute_th_used_time_off")
    th_count_member_selected = fields.Boolean(string='count member', compute="_compute_count_member")
    th_holiday_status_name = fields.Char(string=' ', compute="_compute_th_holiday_status_name")
    th_requires_allocation = fields.Selection(related="holiday_status_id.th_check_type")
    th_total_leave_of_this_year = fields.Float(compute="_compute_th_total_leave_of_this_year")
    name = fields.Char('Reason', compute='_compute_description', inverse='_inverse_description',
                       search='_search_description', compute_sudo=False, required=True)

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_th_total_leave_of_this_year(self):
        for rec in self:
            total = sum(
                self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id), ('holiday_status_id','=',rec.holiday_status_id.id),('state','=','validate')]).mapped('number_of_days'))

            rec.th_total_leave_of_this_year = total


    @api.depends('holiday_status_id')
    def _compute_th_holiday_status_name(self):
        for rec in self:
            rec.th_holiday_status_name = rec.holiday_status_id.name



    @api.depends('holiday_status_id', 'employee_id')
    def _compute_th_used_time_off(self):
        for rec in self:
            strat_date = datetime.combine(fields.Date.today().replace(day=1, month=1), time.min)
            end_date = datetime.combine(fields.Date.today().replace(day=31, month=12), time.max)
            used_time_off = self.env['th.used.time.off'].search([('th_employee_id', '=', rec.employee_id.id), ('th_leave_type_id', '=', rec.holiday_status_id.id), ('th_date', '>=', strat_date), ('th_date', '<=', end_date)])
            rec.th_used_time_off = [(6, 0, used_time_off.ids)]

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_th_allocation_number_of_days(self):
        starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)
        ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
        for rec in self:
            allocations_is_paid_leave = self.env['hr.leave.allocation'].search([('employee_id', '=', rec.employee_id.id),
                                                                ('state', '=', 'validate'),('holiday_status_id.id','=', rec.holiday_status_id.id),
                                                                ('holiday_status_id.th_check_type', '=', 'is_paid_leave'), ('date_from', '>=', starting_day_of_current_year),
                                                                ('date_to', '<=', ending_day_of_current_year)])
            if allocations_is_paid_leave:
                rec.th_allocation_number_of_days = sum(allocations_is_paid_leave.mapped('number_of_days_display'))
            else:
                rec.th_allocation_number_of_days = 0


    @api.depends('employee_ids')
    def _compute_count_member(self):
        if len(self.employee_ids) > 1:
            for rec in self:
                    rec.th_count_member_selected = True
        else:
            for rec in self:
                    rec.th_count_member_selected = False

    @api.depends('employee_id', 'th_allocation_number_of_days','holiday_status_id')
    def _compute_th_remaining_number_of_days(self):
        starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)
        ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
        for rec in self:
            th_allocation_number_of_days = rec.th_allocation_number_of_days
            allocations = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id), ('state', 'not in', ['refuse']),
                                                       ('holiday_status_id.th_check_type', '=', 'is_paid_leave'),
                                                       ('holiday_status_id','=',rec.holiday_status_id.id),
                                                       ('date_from', '>=', starting_day_of_current_year),
                                                       ('date_to', '<=', ending_day_of_current_year)])

            rec.th_remaining_number_of_days = th_allocation_number_of_days - sum(allocations.mapped('number_of_days_display')) if allocations else rec.th_allocation_number_of_days

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            # We force the company in the domain as we are more than likely in a compute_sudo
            domain = [('company_id', 'in', self.env.company.ids + self.env.context.get('allowed_company_ids', []))]
            result = employee._get_work_days_data_batch(date_from, date_to, domain=domain)[employee.id]

            if self.request_unit_half and result['hours'] > 0:
                result['days'] = 0.5

            date_from = date_from + timedelta(hours= 7)
            date_to = date_to + timedelta(hours= 7)
            th_day_from = date_from.weekday()
            th_day_to = date_to.weekday()

            if date_from.date() == date_to.date() and th_day_from == 5:
                if not self.request_unit_hours:
                    result['days'] = 0.5
            else:
                if result['days'] > 0:
                    for x in range((date_to - date_from).days + 1):
                        if (date_from + relativedelta(days=x)).weekday() == 5:
                            result['days'] = result['days'] - 0.5
                else:
                    result['days'] = 0

            if self.request_unit_half and self.request_date_from_period == 'pm' and th_day_from == th_day_to and th_day_from == 5:
                result['days'] = 0
                result['hours'] = 0

            return result

        today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
        days = hours / (today_hours or HOURS_PER_DAY) if not self.request_unit_half else 0.5
        return {'days': days, 'hours': hours}


    @api.depends('holiday_status_id.requires_allocation', 'validation_type', 'employee_id', 'date_from', 'date_to')
    def _compute_from_holiday_status_id(self):
        invalid_self = self.filtered(lambda leave: not leave.date_to or not leave.date_from)
        if invalid_self:
            invalid_self.update({'holiday_allocation_id': False})
            self = self - invalid_self
        if not self:
            return
        allocations = self.env['hr.leave.allocation'].search_read(
            [
                ('holiday_status_id', 'in', self.holiday_status_id.ids),
                ('employee_id', 'in', self.employee_id.ids),
                ('state', '=', 'validate'),
                '|',
                ('date_to', '>=', min(self.mapped('date_to'))),
                '&',
                ('date_to', '=', False),
                ('date_from', '<=', max(self.mapped('date_from'))),
            ], ['id', 'date_from', 'date_to', 'holiday_status_id', 'employee_id', 'max_leaves', 'taken_leave_ids'], order="date_to, id"
        )
        allocations_dict = defaultdict(lambda: [])
        for allocation in allocations:
            allocation['taken_leaves'] = self.env['hr.leave'].browse(allocation.pop('taken_leave_ids'))\
                .filtered(lambda leave: leave.state in ['confirm', 'validate', 'validate1'])
            allocations_dict[(allocation['holiday_status_id'][0], allocation['employee_id'][0])].append(allocation)

        for leave in self:
            if leave.holiday_status_id.requires_allocation == 'yes' and leave.date_from and leave.date_to:
                found_allocation = False
                date_to = leave.date_to.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
                date_from = leave.date_from.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
                leave_unit = 'number_of_%s_display' % ('hours' if leave.leave_type_request_unit == 'hour' else 'days')
                for allocation in allocations_dict[(leave.holiday_status_id.id, leave.employee_id.id)]:
                    date_to_check = allocation['date_to'] >= date_to if allocation['date_to'] else True
                    date_from_check = allocation['date_from'] <= date_from
                    if (date_to_check and date_from_check):
                        allocation_taken_leaves = allocation['taken_leaves'] - leave
                        allocation_taken_number_of_units = sum(allocation_taken_leaves.mapped(leave_unit))
                        leave_number_of_units = leave[leave_unit]
                        if allocation['max_leaves'] >= allocation_taken_number_of_units + leave_number_of_units:
                            found_allocation = allocation['id']
                            break
                leave.holiday_allocation_id = self.env['hr.leave.allocation'].browse(found_allocation) if found_allocation else False
            else:
                leave.holiday_allocation_id = False

    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()


        if leaves:
            raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

        if any(holiday.state not in ['confirm', 'validate1','validate2'] and holiday.validation_type != 'no_validation' for holiday in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})

        leaves_second_approver = self.env['hr.leave']
        leaves_first_approver = self.env['hr.leave']

        for leave in self:
            if leave.validation_type == 'both':
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave

            if leave.holiday_type != 'employee' or\
                (leave.holiday_type == 'employee' and len(leave.employee_ids) > 1):
                if leave.holiday_type == 'employee':
                    employees = leave.employee_ids
                elif leave.holiday_type == 'category':
                    employees = leave.category_id.employee_ids
                elif leave.holiday_type == 'company':
                    employees = self.env['hr.employee'].search([('company_id', '=', leave.mode_company_id.id)])
                else:
                    employees = leave.department_id.member_ids

                conflicting_leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True
                ).search([
                    ('date_from', '<=', leave.date_to),
                    ('date_to', '>', leave.date_from),
                    ('state', 'not in', ['cancel', 'refuse']),
                    ('holiday_type', '=', 'employee'),
                    ('employee_id', 'in', employees.ids)])

                if conflicting_leaves:
                    # YTI: More complex use cases could be managed in master
                    if leave.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                        raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

                    # keep track of conflicting leaves states before refusal
                    target_states = {l.id: l.state for l in conflicting_leaves}
                    conflicting_leaves.action_refuse()
                    split_leaves_vals = []
                    for conflicting_leave in conflicting_leaves:
                        if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
                            continue

                        # Leaves in days
                        if conflicting_leave.date_from < leave.date_from:
                            before_leave_vals = conflicting_leave.copy_data({
                                'date_from': conflicting_leave.date_from.date(),
                                'date_to': leave.date_from.date() + timedelta(days=-1),
                                'state': target_states[conflicting_leave.id],
                            })[0]
                            before_leave = self.env['hr.leave'].new(before_leave_vals)
                            before_leave._compute_date_from_to()

                            # Could happen for part-time contract, that time off is not necessary
                            # anymore.
                            # Imagine you work on monday-wednesday-friday only.
                            # You take a time off on friday.
                            # We create a company time off on friday.
                            # By looking at the last attendance before the company time off
                            # start date to compute the date_to, you would have a date_from > date_to.
                            # Just don't create the leave at that time. That's the reason why we use
                            # new instead of create. As the leave is not actually created yet, the sql
                            # constraint didn't check date_from < date_to yet.
                            if before_leave.date_from < before_leave.date_to:
                                split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
                        if conflicting_leave.date_to > leave.date_to:
                            after_leave_vals = conflicting_leave.copy_data({
                                'date_from': leave.date_to.date() + timedelta(days=1),
                                'date_to': conflicting_leave.date_to.date(),
                                'state': target_states[conflicting_leave.id],
                            })[0]
                            after_leave = self.env['hr.leave'].new(after_leave_vals)
                            after_leave._compute_date_from_to()
                            # Could happen for part-time contract, that time off is not necessary
                            # anymore.
                            if after_leave.date_from < after_leave.date_to:
                                split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

                    split_leaves = self.env['hr.leave'].with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                        leave_skip_state_check=True
                    ).create(split_leaves_vals)

                    split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

                values = leave._prepare_employees_holiday_values(employees)
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    no_calendar_sync=True,
                    leave_skip_state_check=True,
                ).create(values)

                leaves._validate_leave_request()

        leaves_second_approver.write({'second_approver_id': current_employee.id})
        leaves_first_approver.write({'first_approver_id': current_employee.id})

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        return True


    def action_approve(self):
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})

        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.sudo().message_post(
                body=_(
                    'Your %(leave_type)s planned from %(date_from)s to %(date_to)s has been accepted',
                    leave_type=holiday.holiday_status_id.display_name,
                    date_from=holiday.date_from.strftime("%d/%m/%Y"),
                    date_to=holiday.date_to.strftime("%d/%m/%Y")
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids
            )

        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        for rec in self:
            for date in range((rec.date_to - rec.date_from).days + 1):
                number_of_days = 0
                if (rec.date_from + relativedelta(days=date)).weekday() == 6:
                    continue
                elif (rec.date_from + relativedelta(days=date)).weekday() == 5:
                    if rec.leave_type_request_unit == 'hour':
                        number_of_days = 4/8 if rec.number_of_hours_display > 4 else rec.number_of_hours_display/8
                    else:
                        number_of_days = 0.5 if rec.number_of_days > 0.5 else rec.number_of_days
                else:
                    if rec.leave_type_request_unit == 'hour':
                        number_of_days = 8/8 if rec.number_of_hours_display > 8 else rec.number_of_hours_display/8
                    else:
                        number_of_days = 1 if rec.number_of_days > 1 else rec.number_of_days
                for employee in rec.employee_ids:
                    self.env['th.used.time.off'].create({'th_duration_display': f"{float(number_of_days)} day",
                                                         'th_duration_display_vn': f"{float(number_of_days)} ngày",
                                                         'th_date': rec.date_from + relativedelta(days=date),
                                                         'th_employee_id': employee.id,
                                                         'th_leave_type_id': rec.holiday_status_id.id,
                                                         'th_leave_id': rec.id
                                                         })
        return True

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(th_hrLeaveType, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         document = etree.XML(res['arch'])
    #         if 'holiday_type' in res['fields']:
    #             if self._context['lang'] == 'vi_VN':
    #                 res['fields']['holiday_type']['selection'] = [
    #                     ('employee', 'Nhân viên'),
    #                     ('company', 'Công ty'),
    #                     ('department', 'Bộ Phận'),
    #                 ]
    #             else:
    #                 res['fields']['holiday_type']['selection'] = [
    #                     ('employee', 'By Employee'),
    #                     ('company', 'By Company'),
    #                     ('department', 'By Department'),
    #                 ]
    #
    #         res['arch'] = etree.tostring(document, encoding='unicode')
    #     return res

    def th_action_reason(self):
        try:
            form_view_id = self.env.ref("th_time_off.th_hr_leave_reason_view_form").id
        except Exception as e:
            form_view_id = False
        return {
                'type': 'ir.actions.act_window',
                'name': _('Would you like to refuse this leave?'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.leave',
                'views': [(form_view_id, 'form')],
                'target': 'new',
                'res_id': self.id
            }

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').sudo().write({'active': False})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                if holiday.th_reason_refuse:
                    holiday.message_post(
                        body=_('Your %(leave_type)s planned on %(date)s has been refused. Reason: %(th_reason)s',
                        leave_type=holiday.holiday_status_id.display_name,
                        date=holiday.date_from,
                        th_reason = holiday.th_reason_refuse),
                        partner_ids=holiday.employee_id.user_id.partner_id.ids)
                else:
                    holiday.message_post(
                        body=_('Your %(leave_type)s planned on %(date)s has been refused.',
                        leave_type=holiday.holiday_status_id.display_name,
                        date=holiday.date_from),
                        partner_ids=holiday.employee_id.user_id.partner_id.ids)
        for rec in self:
            self.env['th.used.time.off'].search([('th_leave_id', '=', rec.id), ('th_employee_id', '=', rec.employee_id.id)]).unlink()

        self.activity_update()
        return True

    def get_remain_day(self, employee_ids):
        hr_leave_type = self.env['hr.leave.type'].search([])
        return hr_leave_type.get_employees_days_th(employee_ids)

    def get_name_holiday(self):
        return self.holiday_status_id.name

    def get_type_time_off(self):
        return {'id': self.env['hr.leave.type'].search([('th_check_type', '=', 'is_paid_leave')]).id}

    def open_view_help(self):
        group_administration = False
        group_officer = False
        group_user = False
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            group_administration = '3'
        elif self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            group_officer = '2'
        else:
            group_user = '1'
        return {'type': 'ir.actions.act_window',
                'res_model': 'help.hr.leave',
                'view_mode': 'form',
                'views': [(self.env.ref('th_time_off.th_help_hr_leave').id, 'form')],
                'res_id': 1,
                'target': 'new',
                'context': {'invisible_buttons': True, 'group_administration': group_administration, 'group_officer':group_officer, 'group_user': group_user},
                'flags': {'form': {'action_buttons': False}}
                }

    @api.model_create_multi
    def create(self, vals_list):
        holidays = super(th_hrLeaveType, self).create(vals_list)
        for rec in holidays:
            rec = rec.sudo()
            if rec.date_from.hour == 0 and rec.date_to.hour == 12:
                if rec.date_to.weekday() == 5 and rec.date_from.weekday() == 5:
                    rec.write({'date_from': rec.date_from + timedelta(hours=1), 'date_to': rec.date_to - timedelta(hours=7)})
                else:
                    rec.write({'date_from': rec.date_from + timedelta(hours=1), 'date_to': rec.date_to - timedelta(hours=2)})

        return holidays

    def create_values_used_time_off(self):
        self.env['th.used.time.off'].search([]).unlink()
        for rec in self.search([('state', '=', 'validate')], order="id"):
            for date in range((rec.date_to - rec.date_from).days+1):
                number_of_days = 0
                if (rec.date_from + relativedelta(days=date)).weekday() == 6:
                    continue
                elif (rec.date_from + relativedelta(days=date)).weekday() == 5:
                    if rec.leave_type_request_unit == 'hour':
                        number_of_days = 4 /8 if rec.number_of_hours_display > 4 else rec.number_of_hours_display/8
                    else:
                        number_of_days = 0.5 if rec.number_of_days > 0.5 else rec.number_of_days
                else:
                    if rec.leave_type_request_unit == 'hour':
                        number_of_days = 8/8 if rec.number_of_hours_display > 8 else rec.number_of_hours_display/8
                    else:
                        number_of_days = 1 if rec.number_of_days > 1 else rec.number_of_days
                for employee in rec.employee_ids:
                    self.env['th.used.time.off'].create({'th_duration_display': f"{float(number_of_days)} day",
                                                         'th_duration_display_vn': f"{float(number_of_days)} ngày",
                                                         'th_date': rec.date_from + relativedelta(days=date),
                                                         'th_employee_id': employee.id,
                                                         'th_leave_type_id': rec.holiday_status_id.id,
                                                         'th_leave_id': rec.id
                                                         })

    def unlink(self):
        for rec in self:
            self.env['th.used.time.off'].search([('th_leave_id', '=', rec.id), ('th_employee_id', '=', rec.employee_id.id)]).unlink()
        return super(th_hrLeaveType, self).unlink()


    @api.constrains('request_date_from','request_date_to')
    def _constrains_action(self):
        for rec in self:
            if rec.request_date_from.year < datetime.today().year:
                if (datetime.today().date() - rec.request_date_from).days > 40:
                    raise UserError(_(f'The start time is incorrect: years less than {datetime.today().year}'))
            elif rec.request_date_to.year > datetime.today().year + 1:
                raise UserError(_(f'The end time is incorrect: years greater than {datetime.today().year + 1}'))

    # xử lý form gửi mail time off
    def name_get(self):
        res = super(th_hrLeaveType, self).name_get()
        for leave in self:
            if self.env.context.get('short_name'):
                if leave.leave_type_request_unit == 'hour':
                    res.append((
                        leave.id,
                        _("%(leave_type)s: %(duration).2f hours on %(date)s",
                          leave_type=leave.holiday_status_id.name,
                          duration=leave.number_of_hours_display,
                          date=fields.Date.to_string(leave.date_from),
                        )
                    ))
                else:
                    display_date = fields.Date.to_string(leave.date_from)
                    if leave.number_of_days > 1:
                        display_date += ' / %s' % fields.Date.to_string(leave.date_to)
                    res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f days (%(start)s)",
                              leave_type=leave.holiday_status_id.name,
                              duration=leave.number_of_days,
                              start=display_date,
                              )
                        ))

            else:
                if leave.holiday_type == 'company':
                    target = leave.mode_company_id.name
                elif leave.holiday_type == 'department':
                    target = leave.department_id.name
                elif leave.holiday_type == 'category':
                    target = leave.category_id.name
                elif leave.employee_id:
                    target = leave.employee_id.name
                else:
                    target = ', '.join(leave.employee_ids.mapped('name'))
                if leave.leave_type_request_unit == 'hour':
                    if self.env.context.get('hide_employee_name') and 'employee_id' in self.env.context.get('group_by',
                                                                                                            []):
                        res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f hours on %(date)s",
                              person=target,
                              leave_type=leave.holiday_status_id.name,
                              duration=leave.number_of_hours_display,
                              date=fields.Date.to_string(leave.date_from),
                              )
                        ))
                    else:
                        res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f hours on %(date)s",
                              person=target,
                              leave_type=leave.holiday_status_id.name,
                              duration=leave.number_of_hours_display,
                              date=fields.Date.to_string(leave.date_from),
                              )
                        ))
                else:
                    display_date = fields.Date.to_string(leave.date_from)
                    if leave.number_of_days > 1:
                        display_date += ' / %s' % fields.Date.to_string(leave.date_to)
                    if self.env.context.get('hide_employee_name') and 'employee_id' in self.env.context.get('group_by', []):
                        res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f days (%(start)s)",
                              leave_type=leave.holiday_status_id.name,
                              duration=leave.number_of_days,
                              start=display_date,
                              )
                        ))
                    else:
                        res.append((
                            leave.id,
                            _("%(leave_type)s: %(duration).2f days (%(start)s)",
                              person=target,
                              leave_type=leave.holiday_status_id.name,
                              duration=leave.number_of_days,
                              start=display_date,
                              )
                        ))
        return res


