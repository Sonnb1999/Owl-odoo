from odoo import fields, models, api, _

class ThProjectTeam(models.Model):
    _name = "th.project.team"
    _description = "Đội dự án ITC"

    name = fields.Char(string="Tên đội", required=1)
    th_team_type = fields.Selection(selection=[('dev', 'Lập trình'), ('qc', 'Kiểm thử'), ('project', 'Dự án')], string="Loại")
    th_manager_id = fields.Many2one(comodel_name="res.users", string="Trưởng nhóm", domain=lambda self: [('id', 'in', self.env.ref("th_project_itc.th_group_project_user").users.ids)])
    th_member_ids = fields.Many2many(comodel_name="res.users", string="Thành viên đội", domain=lambda self: [('id', 'in', self.env.ref("th_project_itc.th_group_project_user").users.ids)])
