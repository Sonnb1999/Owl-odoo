from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    th_aff_team = fields.Many2one('th.aff.ownership.unit', 'Nhóm')
    th_aff_domain = fields.One2many(comodel_name='th.aff.ownership.unit', compute="action_default_team")

    def action_default_team(self):
        teams = self.env['th.aff.ownership.unit'].sudo().search([])
        th_aff_domain = []
        if teams:
            for team in teams:
                if team and self.env.user.id in team.th_member_ids.ids:
                    th_aff_domain += team.ids

        self.th_aff_domain = teams.search([('id', 'in', th_aff_domain)])

    def action_check(self):
        return self.th_action_one_team()

    @api.model
    def do_security_checks(self):
        # Add your security checks here
        user = self.env.user
        group_user = user.has_group('th_affiliate.group_aff_user')
        group_officer = user.has_group('th_affiliate.group_aff_officer')
        group_manager = user.has_group('th_affiliate.group_aff_manager')
        group_admin = user.has_group('th_affiliate.group_aff_administrator')

        teams = self.env['th.aff.ownership.unit'].sudo().search([])
        th_aff_domain = []
        if teams:
            for team in teams:
                if team and user.id in team.th_member_ids.ids:
                    th_aff_domain += team.ids

        if not group_admin and (group_user or group_officer or group_manager):
            if len(th_aff_domain) > 1:
                return self.th_action_choose_team()
            elif len(th_aff_domain) == 1:
                if not user.th_aff_team:
                    user.sudo().write({
                        'th_aff_team': th_aff_domain[0]
                    })
                return self.th_action_one_team()
            else:
                raise ValidationError(_("Bạn đang không thuộc nhóm nào. Vui lòng liên hệ với quản trị viên!"))
        else:
            return self.th_action_one_team()

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
            'name': _('Vui lòng chọn nhóm.'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.env.user.id
        }
