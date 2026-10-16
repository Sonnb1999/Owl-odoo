# -*- coding: utf-8 -*-
from odoo import fields, models


class ThCollaboratorSignConfig(models.Model):
    _inherit = 'th.collaborator.sign.config'

    th_provider = fields.Selection(
        selection_add=[('vnpt_plugin', 'VNPT-CA Plugin (USB Token)')],
        ondelete={'vnpt_plugin': 'set null'})
    th_vnpt_license_key = fields.Text(string='License key VNPT-CA Plugin')

    def _get_provider_sign_mode(self):
        """VNPT-CA Plugin ký trên trình duyệt qua USB Token cắm ở máy người ký."""
        mode = super()._get_provider_sign_mode()
        return 'client' if self.th_provider == 'vnpt_plugin' else mode

    def _get_client_sign_options(self):
        """Bổ sung license key để JS kích hoạt VNPT-CA Plugin trước khi ký."""
        options = super()._get_client_sign_options()
        if self.th_provider == 'vnpt_plugin':
            options['vnpt_license_key'] = self.th_vnpt_license_key or False
        return options
