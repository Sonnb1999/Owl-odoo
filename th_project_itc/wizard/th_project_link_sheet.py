# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProjectShareWizard(models.TransientModel):
    _name = 'th.project.link.sheet'
    _description = 'Project Sharing link sheet'

    th_project_id = fields.Many2one('th.project.project', string="Dự án")
    th_link_sheet = fields.Html("th Link", related='th_project_id.th_link_sheet')
