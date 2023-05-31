from datetime import datetime, time
from email.policy import default
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from lxml import etree
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.tools.safe_eval import safe_eval


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, tracking=False, copy=False, default='draft',
        help="The status is set to 'To Submit', when an allocation request is created." +
        "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
        "\nThe status is 'Refused', when an allocation request is refused by manager." +
        "\nThe status is 'Approved', when an allocation request is approved by manager.")

    th_condition = fields.Selection(
        [('no', 'No condition'), ('yes', 'With condition')], string='Condition', default='no')
    th_model_name = fields.Char('Model name')
    th_domain = fields.Char('Domain', default="[]")

    th_max_leaves = fields.Float(compute='_th_compute_leaves', store=True)
    th_leaves_taken = fields.Float(compute='_th_compute_leaves', store=True)
    th_duration_display = fields.Char('Allocated (Days/Hours)', compute='_th_compute_duration_display',
                                      help="Field allowing to see the allocation duration in days or hours depending on the type_request_unit", store=True)
    th_number_of_hours_display = fields.Float(
        'Duration (hours)', compute='_th_compute_number_of_hours_display',
        help="If Accrual Allocation: Number of hours allocated in addition to the ones you will get via the accrual' system.", store=True)
    th_reason_refuse = fields.Text('Reason')

    def action_validate(self):
        if not self.employee_id:
            return super().action_validate()
        if self.accrual_plan_id and self.accrual_plan_id.transition_mode == 'immediately':
            self._th_process_accrual_plans()
        else:
            self.nextcall = self._get_next_call(
                self.accrual_plan_id.th_period_number, self.accrual_plan_id.th_frequency)
        return super().action_validate()

    def _action_validate_create_childs(self):
        childs = self.env['hr.leave.allocation']
        # In the case we are in holiday_type `employee` and there is only one employee we can keep the same allocation
        # Otherwise we do need to create an allocation for all employees to have a behaviour that is in line
        # with the other holiday_type
        if self.state == 'validate' and (self.holiday_type in ['category', 'department', 'company'] or
                                         (self.holiday_type == 'employee' and len(self.employee_ids) > 1)):
            if self.holiday_type == 'employee':
                employees = self.employee_ids
            elif self.holiday_type == 'category':
                employees = self.category_id.employee_ids
            elif self.holiday_type == 'department':
                employees = self.department_id.member_ids
            else:
                employees = self.env['hr.employee'].search(
                    [('company_id', '=', self.mode_company_id.id)])

            if self.th_condition == 'yes':
                allocation_create_vals = self._prepare_holiday_values(
                    employees.search(safe_eval(self.th_domain)))
            else:
                allocation_create_vals = self._prepare_holiday_values(employees)

            childs += self.with_context(
                mail_notify_force_send=False,
                mail_activity_automation_skip=True
            ).create(allocation_create_vals)
            if childs:
                childs.action_validate()
        return childs
    # th delete allocation 
    def activity_update(self):
        to_clean, to_do = self.env['hr.leave.allocation'], self.env['hr.leave.allocation']
        for allocation in self:
            note = _(
                'New Allocation Request created by %(user)s: %(count)s Days of %(allocation_type)s',
                user=allocation.create_uid.name,
                count=allocation.number_of_days,
                allocation_type=allocation.holiday_status_id.name
            )
            if allocation.state == 'draft':
                to_clean |= allocation
            elif allocation.state == 'confirm':
                pass
                # allocation.activity_schedule(
                #     'hr_holidays.mail_act_leave_allocation_approval',
                #     note=note,
                #     user_id=allocation.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif allocation.state == 'validate1':
                allocation.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval'])
                # allocation.activity_schedule(
                #     'hr_holidays.mail_act_leave_allocation_second_approval',
                #     note=note,
                #     user_id=allocation.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif allocation.state == 'validate':
                pass
                # to_do |= allocation
            elif allocation.state == 'refuse':
                to_clean |= allocation
        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_allocation_approval', 'hr_holidays.mail_act_leave_allocation_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval', 'hr_holidays.mail_act_leave_allocation_second_approval'])


    def _end_of_year_accrual(self):
        first_day_this_year = fields.Date.today() + relativedelta(month=1, day=1)
        for allocation in self:
            if allocation.action_with_unused_accruals == 'lost':
                allocation.write(
                    {'number_of_days': allocation.leaves_taken, 'lastcall': first_day_this_year})

    def _get_next_call(self, period, frequency):
        now = fields.Datetime.now()
        if not frequency or not period:
            return
        if frequency == 'day':
            return now + relativedelta(days=period)
        elif frequency == 'month':
            return now + relativedelta(months=period, day=1)
        elif frequency == 'year':
            return now + relativedelta(years=period, month=1, day=1)

    def _th_process_accrual_plans(self):
        for rec in self:
            rec.nextcall = rec._get_next_call(
                rec.accrual_plan_id.th_period_number, rec.accrual_plan_id.th_frequency)
            th_max_days = 0
            if rec.accrual_plan_id.th_max_days == 1:
                th_max_days += (rec.accrual_plan_id.th_max_days + 1) if rec.accrual_plan_id.th_period == 'day' else (rec.accrual_plan_id.th_max_days + 1) * 8
            else:
                th_max_days += rec.accrual_plan_id.th_max_days
            if rec.accrual_plan_id.th_period == 'day':
                if th_max_days > rec.number_of_days + rec.accrual_plan_id.th_days_add:
                    rec.number_of_days += rec.accrual_plan_id.th_days_add
            else:
                if th_max_days > rec.number_of_days * 8 + rec.accrual_plan_id.th_days_add:
                    rec.number_of_days += rec.accrual_plan_id.th_days_add / 8

    @api.model
    def _update_accrual(self):
        today = datetime.combine(fields.Date.today(), time(0, 0, 0))
        this_year_first_day = today + relativedelta(day=1, month=1)
        end_of_year_allocations = self.search(
            [('allocation_type', '=', 'accrual'), ('state', '=', 'validate'), ('accrual_plan_id', '!=', False),
             ('employee_id', '!=', False),
             '|',
             ('date_to', '=', False),
             ('date_to', '>', fields.Datetime.now()),
             ('lastcall', '<', this_year_first_day)])
        end_of_year_allocations._end_of_year_accrual()
        end_of_year_allocations.flush_model()
        self._action_validate_create_childs_to_year()
        allocations = self.search(
            [('allocation_type', '=', 'accrual'), ('state', '=', 'validate'), ('accrual_plan_id', '!=', False),
             ('employee_id', '!=', False),
             '|', ('date_to', '=', False),
             ('date_to', '>', fields.Datetime.now()),
             '|', ('nextcall', '=', False), ('nextcall', '<=', today)])
        allocations._th_process_accrual_plans()

    def _action_validate_create_childs_to_year(self):
        childs = self.env['hr.leave.allocation']
        th_set_domain = self.search([('th_condition','=', 'yes')])
        if th_set_domain:
            for record in th_set_domain:
                th_employee_domain = self.env['hr.employee'].search(safe_eval(record.th_domain))
                employee_not_alloction = [i for i in th_employee_domain.ids if i not in self.search([('parent_id', '=', record.id)]).mapped('employee_id').ids]
                th_employee  = self.env['hr.employee'].search([('id','in',employee_not_alloction)])
                # th_employee_allocation =  self.search([('employee_id','in',th_employee_domain.ids)])
                
                th_allocation_plus_day = self._plus_day(th_employee,record)
                if th_allocation_plus_day:
                    childs += self.create(th_allocation_plus_day)
        return childs

    def _plus_day(self, employees,record):
        record.ensure_one()
        return [{
            'name': record.name,
            'holiday_type': 'employee',
            'holiday_status_id': record.holiday_status_id.id,
            'notes': record.notes,
            'number_of_days': record.number_of_days,
            'parent_id': record.id,
            'employee_id': employee.id,
            'employee_ids': [(6, 0, [employee.id])],
            'state': 'validate',
            'allocation_type': record.allocation_type,
            'date_from': record.date_from,
            'date_to': record.date_to,
            'accrual_plan_id': record.accrual_plan_id.id,
        } for employee in employees]

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(HolidaysAllocation, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #
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
    #         res['arch'] = etree.tostring(document, encoding='unicode')
    #     return res

    @api.depends('max_leaves', 'leaves_taken', 'taken_leave_ids.state')
    def _th_compute_leaves(self):
        for allocation in self:
            allocation.th_max_leaves = allocation.number_of_hours_display if allocation.type_request_unit == 'hour' else allocation.number_of_days
            if allocation.holiday_status_id.th_check_type == 'is_paid_leave':
                if allocation.holiday_status_id.request_unit == 'hour':
                    allocation.th_leaves_taken = allocation.leaves_taken/8
                else:
                    allocation.th_leaves_taken = allocation.leaves_taken

    @api.depends('duration_display', 'taken_leave_ids.state')
    def _th_compute_duration_display(self):
        for allocation in self:
            if allocation.holiday_status_id.request_unit == 'hour':
                allocation.th_duration_display = allocation.number_of_hours_display/8
            else:
                allocation.th_duration_display = allocation.number_of_days

    @api.depends('number_of_hours_display')
    def _th_compute_number_of_hours_display(self):
        for allocation in self:
            allocation.th_number_of_hours_display = allocation.number_of_hours_display

    def th_action_reason(self):
        try:
            form_view_id = self.env.ref("th_time_off.hr_leave_allocation_reason_view_form").id
        except Exception as e:
            form_view_id = False
        return {
                'type': 'ir.actions.act_window',
                'name': 'Would you refuse this leave?',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.leave.allocation',
                'views': [(form_view_id, 'form')],
                'target': 'new',
                'res_id': self.id
            }
