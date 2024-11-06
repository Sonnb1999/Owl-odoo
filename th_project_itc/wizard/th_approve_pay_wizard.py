from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ThApprovePayWizard(models.TransientModel):
    _name = "th.approve.pay.wizard"
    _description = "Yêu cầu phê duyệt"

    th_type = fields.Selection(selection=[('raw_materials', 'Thanh toán học liệu thô'), ('input_data', 'Thanh toán nhập liệu')], string="Loại thanh toán", required=1)

    def th_action_approve_wizard(self):
        ids = self.env.context['active_ids']  # selected record ids
        tasks = self.env["th.project.task"].browse(ids)
        for task in tasks:
            if not task.th_is_pay:
                raise ValidationError(_("Dự án này không phải là dự án cần thanh toán."))
            if task.th_type_input_data == 'pending' and task.th_type_input_data == 'pending':
                raise ValidationError(_("Bạn không thể có 2 phê duyệt thanh toán cùng 1 lúc."))

            if task.th_type_raw_material == 'approved' and self.th_type == 'raw_materials':
                raise ValidationError(_("Đã phê duyệt thanh toán học liệu thô."))

            if task.th_type_input_data == 'approved' and self.th_type == 'input_data':
                raise ValidationError(_("Đã phê duyệt thanh toán nhập liệu."))

            vals = {
                'th_is_check_again': False,
            }
            if self.th_type == 'raw_materials':
                vals['th_type_raw_material'] = 'pending'
            else:
                vals['th_type_input_data'] = 'pending'
            task.write(vals)
