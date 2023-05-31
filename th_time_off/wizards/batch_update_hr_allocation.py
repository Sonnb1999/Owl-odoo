from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class batch_update_leave_allocation_wizard(models.TransientModel):
    _name = "allocation.batchupdate.wizard"
    _description = "Batch update for allocation model"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
        ], string='Status', default='draft',
        help="The status is set to 'To Submit', when an allocation request is created." +
        "\nThe status is 'To Approve', when an allocation request is confirmed by user." +
        "\nThe status is 'Refused', when an allocation request is refused by manager." +
        "\nThe status is 'Approved', when an allocation request is approved by manager.")

   

    def multi_update(self):
        ids = self.env.context['active_ids']  # selected record ids
        leaves = self.env["hr.leave.allocation"].browse(ids)
        if self.state == 'draft':
            leaves.action_draft()
        elif self.state == 'confirm':
            leaves.action_confirm()
        elif self.state == 'refuse':
            leaves.action_refuse()
        elif self.state == 'cancel':
            leaves.write({'state': self.state})
        else:
            leaves.action_validate()
