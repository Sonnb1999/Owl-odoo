# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProjectProjectStage(models.Model):
    _name = 'th.project.project.stage'
    _description = 'Project Stage'
    _order = 'sequence, id'

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=50)
    name = fields.Char(required=True, translate=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template', domain=[('model', '=', 'th.project.project')],
        help="If set, an email will be automatically sent to the customer when the project reaches this stage.")
    fold = fields.Boolean('Folded in Kanban',
        help="If enabled, this stage will be displayed as folded in the Kanban view of your projects. Projects in a folded stage are considered as closed.")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, default=lambda self: self.env.company)
