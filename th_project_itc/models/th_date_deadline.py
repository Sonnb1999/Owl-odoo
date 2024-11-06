import json
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ThDateDeadline(models.Model):
    _name = "th.date.deadline"
    _description = "Đội dự án ITC"

    name = fields.Char(string="Tên đội")
    th_evaluate_type = fields.Selection(selection=[('fast', 'Nhanh'), ('slow', 'Chậm'), ('ontime', 'Đúng tiến độ')], string="Đánh giá", compute="_compute_th_evaluate_type")
    th_project_task_id = fields.Many2one("th.project.task", string="Nhiệm vụ")
    th_stage = fields.Many2one("th.project.task.type", string="Giai đoạn")
    th_deadline_start = fields.Date(string="Ngày bắt đầu kế hoạch")
    th_deadline_end = fields.Date(string="Ngày kết thúc kế hoạch")
    th_date_finish = fields.Date(string="Ngày kết thúc thực tế")
    th_date_start = fields.Date(string="Ngày bắt đầu thực tế")
    th_description = fields.Char(string="Ghi chú")
    th_domain_stage = fields.Char(string="domain trạng thái", compute="_compute_th_domain_stage")

    @api.depends("th_project_task_id")
    def _compute_th_domain_stage(self):
        for rec in self:
            domain = []
            if rec.th_project_task_id:
                domain.append(('th_project_ids', '=', rec.th_project_task_id.project_id.id))
            rec.th_domain_stage = json.dumps(domain)

    def get_th_evaluate_type_value(self):
        value = ''
        for rec in self:
            if rec.th_evaluate_type == 'fast':
                value = "Nhanh"
            if rec.th_evaluate_type == 'slow':
                value = "Chậm"
            if rec.th_evaluate_type == 'ontime':
                value = "Đúng tiến độ"
        return value

    @api.depends("th_deadline_end", "th_date_finish")
    def _compute_th_evaluate_type(self):
        for rec in self:
            if rec.th_deadline_end and rec.th_date_finish:
                if rec.th_deadline_end < rec.th_date_finish:
                    rec.th_evaluate_type = "slow"
                elif rec.th_deadline_end > rec.th_date_finish:
                    rec.th_evaluate_type = "fast"
                else:
                    rec.th_evaluate_type = "ontime"
            elif rec.th_deadline_end and not rec.th_date_finish:
                if rec.th_deadline_end >= fields.Date.today():
                    rec.th_evaluate_type = False
                else:
                    rec.th_evaluate_type = "slow"
            else:
                rec.th_evaluate_type = False

    @api.constrains('th_stage')
    def _check_stage_exist(self):
        for rec in self:
            if self.search_count([('th_project_task_id', '=', rec.th_project_task_id.id), ('th_stage', '=', rec.th_stage.id),('id', '!=', rec.id)]) > 0:
                raise ValidationError("Trạng thái đã có, vui lòng không tạo lại!")

    @api.constrains('th_deadline_start', 'th_deadline_end')
    def _check_date_range(self):
        for rec in self:
            if rec.th_deadline_end and rec.th_deadline_start and rec.th_deadline_end < rec.th_deadline_start:
                raise ValidationError("Ngày kết thúc không thể nhỏ hơn ngày bắt đầu.")

