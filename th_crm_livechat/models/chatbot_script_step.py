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

    is_question_name = fields.Boolean('Ask name')

    # Set data
    def _chatbot_prepare_customer_values(self, mail_channel, create_partner=True, update_partner=True):

        partner = False
        user_inputs = mail_channel._chatbot_find_customer_values_in_messages({
            'question_email': 'email',
            'question_phone': 'phone',
            'free_input_single': 'name',
        })
        input_email = user_inputs.get('email', False)
        input_phone = user_inputs.get('phone', False)
        input_name = user_inputs.get('name', False)


        if self.env.user._is_public() and (create_partner or (input_name and (input_phone or input_email))):
            partner = self.env['res.partner'].sudo().search(
                [
                    '|', '&', ('email', '=', input_email), ('phone', '=', input_phone), ('activity_ids', '=', True)
                ])
            if partner:
                partner = partner
            else:
                partner = self.env['res.partner'].create({
                    'name': input_name or input_email,
                    'email': input_email,
                    'phone': input_phone,
                })
        elif not self.env.user._is_public():
            partner = self.env.user.partner_id
            if update_partner:
                # update email/phone value from partner if not set
                update_values = {}
                if input_email and not partner.email:
                    update_values['email'] = input_email
                if input_phone and not partner.phone:
                    update_values['phone'] = input_phone
                if update_values:
                    partner.write(update_values)

        description = Markup('')
        if input_name:
            description += Markup('%s<strong>%s</strong><br>') % (_('Name of contact: '), input_name)
        if input_email:
            description += Markup('%s<strong>%s</strong><br>') % (_('Please contact me on: '), input_email)
        if input_phone:
            description += Markup('%s<strong>%s</strong><br>') % (_('Please call me on: '), input_phone)
        if description:
            description += Markup('<br>')

        return {
            'partner': partner,
            'email': input_email,
            'phone': input_phone,
            'description': description,
        }

    # Step answer
    def _process_answer(self, mail_channel, message_body):
        self.ensure_one()

        user_text_answer = html2plaintext(message_body)
        if self.step_type == 'question_email' and not email_normalize(user_text_answer):
            # if this error is raised, display an error message but do not go to next step
            raise ValidationError(_('"%s" is not a valid email.', user_text_answer))

        if self.step_type in ['question_email', 'question_phone'] or (
                self.step_type in ['free_input_single'] and self.is_question_name):
            chatbot_message = self.env['chatbot.message'].search([
                ('mail_channel_id', '=', mail_channel.id),
                ('script_step_id', '=', self.id),
            ], limit=1)

            if chatbot_message:
                chatbot_message.write({'user_raw_answer': message_body})
                self.env.flush_all()

        return self._fetch_next_step(mail_channel.chatbot_message_ids.user_script_answer_id)

    def _process_step_create_lead(self, mail_channel):
        customer_values = self._chatbot_prepare_customer_values(
            mail_channel, create_partner=False, update_partner=True)
        if self.env.user._is_public() and not customer_values['partner']:
            create_values = {
                'email_from': customer_values['email'],
                'phone': customer_values['phone'],
            }
        else:
            partner = self.env.user.partner_id
            create_values = {
                'partner_id': partner.id,
                'company_id': partner.company_id.id,
            }

        create_values.update(self._chatbot_crm_prepare_lead_values(
            mail_channel, customer_values['description']))

        self.env['crm.lead'].create(create_values)
