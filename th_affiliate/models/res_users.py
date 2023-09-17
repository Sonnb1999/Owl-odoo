from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    th_aff_team = fields.Many2one('th.aff.ownership.unit', 'Nhóm')
    th_aff_domain = fields.Char(compute="action_default_team")

    def action_default_team(self):
        teams = self.env['th.aff.ownership.unit'].sudo().search([])
        th_aff_domain = []
        if teams:
            for team in teams:
                if team and self.id in team.th_member_ids.ids:
                    th_aff_domain += team.ids

        self.th_aff_domain = th_aff_domain

    def action_check(self):
        return self.th_action_one_team()

    @api.model
    def do_security_checks(self):
        # Add your security checks here
        if self.env.user.has_group('th_affiliate.group_aff_officer'):
            return self.th_action_one_team()
        else:
            return self.th_action_choose_team()

    def th_action_one_team(self):
        # Execute your desired action
        return {
            'name': _('Giao bài'),
            'type': 'ir.actions.act_window',
            'res_model': 'th.link.seeding',
            'view_mode': 'tree,form',
        }

    def th_action_choose_team(self):
        try:
            form_view_id = self.env.ref("th_affiliate.th_hr_aff_team_view_form").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bạn chọn team nào?'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.env.user.id
        }
