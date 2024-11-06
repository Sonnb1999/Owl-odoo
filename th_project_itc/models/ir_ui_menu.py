# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _load_menus_blacklist(self):
        res = super()._load_menus_blacklist()
        if not self.env.user.has_group('th_project_itc.th_group_project_manager'):
            res.append(self.env.ref('th_project_itc.th_rating_rating_menu_project').id)
        if self.env.user.has_group('th_project_itc.th_group_project_stages'):
            res.append(self.env.ref('th_project_itc.th_menu_projects').id)
            res.append(self.env.ref('th_project_itc.th_menu_projects_config').id)
        return res
