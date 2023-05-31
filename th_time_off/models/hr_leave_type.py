from odoo import models, fields, api
from lxml import etree


class th_HolidaysRequest(models.Model):
    _inherit = 'hr.leave.type'

    leave_validation_type = fields.Selection(default="manager")

    responsible_id = fields.Many2one(
        'res.users', 'Responsible Time Off Officer',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'hr_holidays.group_hr_holidays_user').id)],
        help="Choose the Time Off Officer who will be notified to approve allocation or Time Off request")

    th_check_type = fields.Selection([
        ('is_paid_leave', 'Paid Leave'),
        ('is_paternity_leave', 'Paternity Leave'),  # for dad
        ('is_maternity_leave', 'Maternity Leave'),  # for mom
        ('is_wedding_leave', 'Wedding Leave'),
        ('is_funeral_leave', 'Funeral Leave'),
    ], string="Type check")

    employee_requests = fields.Selection([
        ('yes', 'Extra Days Requests Allowed'),
        ('no', 'Not Allowed')], default="no", required=True, string="Employee Requests")

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     ret_val = super().fields_view_get(view_id=view_id,view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         document = etree.XML(ret_val['arch'])
    #         if 'allocation_validation_type' in ret_val['fields']:
    #             if self._context['lang'] == 'vi_VN':
    #                 ret_val['fields']['allocation_validation_type']['selection'] = [
    #                     ('no', 'Không cần xác thực'), ('officer', 'Được chấp thuận bởi nhân viên quản lý nghỉ phép')]
    #             else:
    #                 ret_val['fields']['allocation_validation_type']['selection'] = [
    #                     ('no', 'No validation needed'), ('officer', 'Approved by Time Off Officer')]
    #         ret_val['arch'] = etree.tostring(document, encoding='unicode')
    #     return ret_val

    def get_employees_days_th(self, employee_ids):
        result = {
            employee_id: {
                leave_type.id: {
                    'allocation': leave_type.requires_allocation,
                    'type_class': leave_type.request_unit,
                    'name': leave_type.name,
                    'max_leaves': 0,
                    'leaves_taken': 0,
                    'remaining_leaves': 0,
                    'virtual_remaining_leaves': 0,
                    'virtual_leaves_taken': 0,
                } for leave_type in self
            } for employee_id in employee_ids
        }

        requests = self.env['hr.leave'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', self.ids)
        ])

        for request in requests:
            status_dict = result[request.employee_id.id][request.holiday_status_id.id]
            status_dict['virtual_remaining_leaves'] -= (request.number_of_hours_display
                                                    if request.leave_type_request_unit == 'hour'
                                                    else request.number_of_days)
            status_dict['virtual_leaves_taken'] += (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)
            if request.state == 'validate':
                status_dict['leaves_taken'] += (request.number_of_hours_display
                                            if request.leave_type_request_unit == 'hour'
                                            else request.number_of_days)
                status_dict['remaining_leaves'] -= (request.number_of_hours_display
                                                if request.leave_type_request_unit == 'hour'
                                                else request.number_of_days)

        for allocation in allocations.sudo():
            status_dict = result[allocation.employee_id.id][allocation.holiday_status_id.id]
            if allocation.state == 'validate':
                # note: add only validated allocation even for the virtual
                # count; otherwise pending then refused allocation allow
                # the employee to create more leaves than possible
                status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                          if allocation.type_request_unit == 'hour'
                                                          else allocation.number_of_days)
                status_dict['max_leaves'] += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)

                status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                    if allocation.type_request_unit == 'hour'
                                                    else allocation.number_of_days)
        a = result
        return result

    @api.model
    def delete_values_hr_leave_type(self):
        for rec in self.sudo().search([('name', 'in', ['Sick Time Off', 'Compensatory Days', 'Paid Time Off', 'Unpaid'])]):
            rec.sudo().write({'active': False})
            