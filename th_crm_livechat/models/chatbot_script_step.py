from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import html2plaintext, is_html_empty, email_normalize, plaintext2html

from collections import defaultdict
from markupsafe import Markup


class ChatbotScriptStep(models.Model):
    _inherit = 'chatbot.script.step'

    def _chatbot_prepare_customer_values(self, mail_channel, create_partner=True, update_partner=True):
        a = super()._chatbot_prepare_customer_values(mail_channel, create_partner, update_partner)

        print('agsffsfsdfdf')