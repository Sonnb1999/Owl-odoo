from odoo import _, api, models, fields
from odoo.tools import email_normalize, html2plaintext, is_html_empty, plaintext2html


class ChatbotScript(models.Model):
    _inherit = 'chatbot.script'

    @api.depends('script_step_ids.step_type')
    def _compute_first_step_warning(self):
        for script in self:
            allowed_first_step_types = [
                'question_selection',
                'question_email',
                'question_name',
                'question_phone',
                'free_input_single',
                'free_input_multi',
            ]
            welcome_steps = script.script_step_ids and script._get_welcome_steps()
            if welcome_steps and welcome_steps[-1].step_type == 'forward_operator':
                script.first_step_warning = 'first_step_operator'
            elif welcome_steps and welcome_steps[-1].step_type not in allowed_first_step_types:
                script.first_step_warning = 'first_step_invalid'
            else:
                script.first_step_warning = False
