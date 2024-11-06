from odoo import fields, models

class TaskAssignWizard(models.TransientModel):
    _name = "th.task.assign"
    _description = "Lựa chọn giao nhiệm vụ"

    th_selec_task_assign = fields.Selection(selection=[('implementer', 'Người thực viện'), ('test', 'Người kiểm thử')], string="Phân công vào", required=1, default="implementer")
    th_task_id = fields.Many2one(comodel_name="th.project.task", string="Nhiệm vụ")

    def th_action_task_assign_wizard(self):
        for rec in self:
            uid = self.env.user.id
            if rec.th_selec_task_assign == 'test':
                rec.th_task_id.write({'th_user_test_ids': [(4, uid)]})
            else:
                rec.th_task_id.write({'user_ids': [(4, uid)]})