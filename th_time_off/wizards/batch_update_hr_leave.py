from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class batch_update_leave_wizard(models.TransientModel):
    _name = "leave.batchupdate.wizard"
    _description = "Batch update for leaves model"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        # ('validate1', ''),
        ('validate', 'Approved')
        ], string='Status', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")

   

    def multi_update(self):
        ids = self.env.context['active_ids']  # selected record ids
        leaves = self.env["hr.leave"].browse(ids)
        if self.state == 'draft':
            leaves.action_draft()
        elif self.state == 'confirm':
            leaves.action_confirm()
        elif self.state == 'refuse':
            leaves.action_refuse()
        else:
            leaves.action_approve()