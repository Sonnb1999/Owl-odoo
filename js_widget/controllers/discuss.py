# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import http
from odoo.http import request
from odoo.addons.mail.controllers.discuss import DiscussController


class DiscussController(DiscussController):

    @http.route('/mail/thread/messages', methods=['POST'], type='json', auth='user')
    def mail_thread_messages(self, thread_model, thread_id, max_id=None, min_id=None, limit=30, th_param=None, **kwargs):
        domain_custom = [
            ('res_id', '=', int(thread_id)),
            ('model', '=', thread_model),
            ('message_type', '!=', 'user_notification'),
        ]

        if th_param:
            domain_custom.append((
                'is_internal', '=', th_param['is_internal']
            ))

        messages = request.env['mail.message']._message_fetch(domain=domain_custom, max_id=max_id, min_id=min_id, limit=limit)
        if not request.env.user._is_public():
            messages.set_message_done()
        return messages.message_format()
