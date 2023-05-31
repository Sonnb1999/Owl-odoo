from odoo import fields, models, api

class ThTimeOff(models.Model):
    _name = "th.used.time.off"
    _description = "Used time off"

    th_number_of_days = fields.Float(string="Number of days")
    th_duration_display = fields.Char(string="Duration")
    th_duration_display_vn = fields.Char(string="Thời lượng")
    th_date = fields.Date(string="Date")
    th_employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    th_leave_type_id = fields.Many2one(comodel_name="hr.leave.type", string="Leave type")
    th_leave_id = fields.Many2one(comodel_name="hr.leave", string="Leave")