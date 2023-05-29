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
        """ Create a lead from channel /lead command
        :param partner: internal user partner (operator) that created the lead;
        :param key: operator input in chat ('/lead Lead about Product')
        """
        # if public user is part of the chat: consider lead to be linked to an
        # anonymous user whatever the participants. Otherwise keep only share
        # partners (no user or portal user) to link to the lead.
        customers = self.env['res.partner']
        # for customer in self.with_context(active_test=False).channel_partner_ids.filtered(
        #         lambda p: p != partner and p.partner_share):
        #     if customer.is_public:
        #         customers = self.env['res.partner']
        #         break
        #     else:
        #         customers |= customer

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
        customers = customers.sudo().search(['|', ('phone', '=', phone), ('email', '=', email)])

        if email != '' and phone != '' and not customers:
            contact_id = self.env['res.partner'].sudo().create({
                'name': name,
                'phone': phone,
                'email': email,
            }).id

        return self.env['crm.lead'].create({
            'name': html2plaintext(list_str[0][5:]),
            'partner_id': customers[0].id if customers else contact_id,
            'user_id': False,
            'team_id': False,
            ''
            'description': self._get_channel_history(),
            'referred': partner.name,
            'source_id': utm_source and utm_source.id,
        })

