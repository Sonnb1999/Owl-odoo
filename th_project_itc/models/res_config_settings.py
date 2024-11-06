# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_project_forecast_itc = fields.Boolean(string="Planning")
    module_hr_timesheet_itc = fields.Boolean(string="Task Logs")
    group_subtask_project_itc = fields.Boolean("Sub-tasks", implied_group="th_project_itc.th_group_subtask_project")
    group_project_rating_itc = fields.Boolean("Customer Ratings", implied_group='th_project_itc.th_group_project_rating')
    group_project_stages_itc = fields.Boolean("Project Stages", implied_group="th_project_itc.th_group_project_stages")
    group_project_recurring_tasks_itc = fields.Boolean("Recurring Tasks", implied_group="th_project_itc.th_group_project_recurring_tasks",default=True)
    group_project_task_dependencies_itc = fields.Boolean("Task Dependencies", implied_group="th_project_itc.th_group_project_task_dependencies")
    group_project_milestone_itc = fields.Boolean('Milestones', implied_group='th_project_itc.th_group_project_milestone', group='base.group_portal,base.group_user')

    # Analytic Accounting
    th_analytic_plan_id = fields.Many2one(
        comodel_name='account.analytic.plan',
        string="Default Plan",
        readonly=False,
        related='company_id.th_analytic_plan_id',
    )

    @api.model
    def _get_basic_project_domain(self):
        return []

    def set_values(self):
        # Ensure that settings on existing projects match the above fields
        projects = self.env["th.project.project"].search([])
        basic_projects = projects.filtered_domain(self._get_basic_project_domain())

        features = {
            # key: (config_flag, is_global), value: project_flag
            ("group_project_rating_itc", True): "rating_active",
            ("group_project_recurring_tasks_itc", True): "allow_recurring_tasks",
            ("group_subtask_project_itc", False): "allow_subtasks",
            ("group_project_task_dependencies_itc", False): "allow_task_dependencies",
            ("group_project_milestone_itc", False): "allow_milestones",
        }

        for (config_flag, is_global), project_flag in features.items():
            config_flag_global = f"th_project_itc.{config_flag}"
            config_feature_enabled = self[config_flag]
            if self.user_has_groups(config_flag_global) != config_feature_enabled:
                if config_feature_enabled and not is_global:
                    basic_projects[project_flag] = config_feature_enabled
                else:
                    projects[project_flag] = config_feature_enabled

        # Hide the task dependency changes subtype when the dependency setting is disabled
        task_dep_change_subtype_id = self.env.ref('th_project_itc.th_mt_task_dependency_change')
        project_task_dep_change_subtype_id = self.env.ref('th_project_itc.th_mt_project_task_dependency_change')
        if task_dep_change_subtype_id.hidden != (not self['group_project_task_dependencies_itc']):
            task_dep_change_subtype_id.hidden = not self['group_project_task_dependencies_itc']
            project_task_dep_change_subtype_id.hidden = not self['group_project_task_dependencies_itc']
        # Hide Project Stage Changed mail subtype according to the settings
        project_stage_change_mail_type = self.env.ref('th_project_itc.th_mt_project_stage_change')
        if project_stage_change_mail_type.hidden == self['group_project_stages_itc']:
            project_stage_change_mail_type.hidden = not self['group_project_stages_itc']

        super().set_values()
