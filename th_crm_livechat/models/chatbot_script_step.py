from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import html2plaintext, is_html_empty, email_normalize, plaintext2html

from collections import defaultdict
from markupsafe import Markup


class ChatbotScriptStep(models.Model):
    _inherit = 'chatbot.script.step'

    step_type = fields.Selection(
        selection_add=[('question_name', 'Name')],
        ondelete={'question_name': 'cascade'}
    )

    def _chatbot_prepare_customer_values(self, mail_channel, create_partner=True, update_partner=True):
        result = super()._chatbot_prepare_customer_values(mail_channel, create_partner, update_partner)

        if not result['partner']:
            pass

        print('agsffsfsdfdf')
