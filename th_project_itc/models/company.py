# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    th_analytic_plan_id = fields.Many2one(
        'account.analytic.plan',
        string="Default Plan",
        check_company=True,
        readonly=False,
        compute="_compute_th_analytic_plan_id",
        help="Default Plan for a new analytic account for projects")

    def _compute_th_analytic_plan_id(self):
        for company in self:
            default_plan = self.env['ir.config_parameter'].with_company(company).sudo().get_param("default_th_analytic_plan_id_%s" % company.id)
            company.th_analytic_plan_id = int(default_plan) if default_plan else False
            if not company.th_analytic_plan_id:
                company.th_analytic_plan_id = self.env['account.analytic.plan'].with_company(company)._get_default()

    def write(self, values):
        for company in self:
            if 'th_analytic_plan_id' in values:
                self.env['ir.config_parameter'].sudo().set_param("default_th_analytic_plan_id_%s" % company.id, values['th_analytic_plan_id'])
        return super().write(values)
