from odoo import models, _
from odoo.tools import html2plaintext


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    def execute_command_lead(self, **kwargs):
        partner = self.env.user.partner_id
        key = kwargs['body']
        if key.strip() == '/lead':
            msg = _('Create a new lead (/lead lead title)')
        else:
            lead = self._convert_visitor_to_lead(partner, key)
            msg = _(
                'Created a new lead: %s',
                lead._get_html_link(),
            )
        self._send_transient_message(partner, msg)

    def _convert_visitor_to_lead(self, partner, key):
        customers = self.env['res.partner']

        utm_source = self.env.ref('crm_livechat.utm_source_livechat', raise_if_not_found=False)
        list_str = key.split(',')

        name = ''
        email = ''
        phone = ''
        contact_id = False

        for val in list_str:
            if '/' not in val and not html2plaintext(val).isdigit() and '@'not in val:
                name = html2plaintext(val)

            if '@' in val:
                email = html2plaintext(val)

            if html2plaintext(val).isdigit():
                phone = html2plaintext(val)
        customers = customers.sudo().search([('phone', '=', phone)])

        if customers and not customers.email and email != '':
            customers.sudo().update({
                'email': email
            })

        if phone != '' and not customers:
            name = name if name != '' else phone if phone != '' else email
            contact_id = self.env['res.partner'].sudo().create({
                'name': name,
                'phone': phone,
                'email': email,
            }).id

        return self.env['crm.lead'].sudo().create({
            'name': html2plaintext(list_str[0][5:]),
            'partner_id': customers[0].id if customers else contact_id,
            'user_id': False,
            'team_id': False,
            ''
            'description': self._get_channel_history(),
            'referred': partner.name,
            'source_id': utm_source and utm_source.id,
        })

