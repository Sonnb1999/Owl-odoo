# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import AccessError


class Digest(models.Model):
    _inherit = 'digest.digest'

    th_kpi_project_task_opened = fields.Boolean('Open Tasks')
    th_kpi_project_task_opened_value = fields.Integer(compute='_compute_project_task_opened_value')

    def _compute_project_task_opened_value(self):
        if not self.env.user.has_group('th_project_itc.th_group_project_user'):
            raise AccessError(_("Do not have access, skip this data for user's digest email"))
        for record in self:
            start, end, company = record._get_kpi_compute_parameters()
            record.kpi_project_task_opened_value = self.env['th.project.task'].search_count([

                ('stage_id.fold', '=', False),
                ('create_date', '>=', start),
                ('create_date', '<', end),
                ('company_id', '=', company.id),
                ('display_project_id', '!=', False),
            ])

    def _compute_kpis_actions(self, company, user):
        res = super(Digest, self)._compute_kpis_actions(company, user)
        res['th_kpi_project_task_opened'] = 'th_project_itc.th_open_view_project_all&menu_id=%s' % self.env.ref('th_project_itc.th_menu_main_pm').id
        return res
