# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import random
import requests
import string

from lxml import html
from werkzeug import urls

from odoo import tools, models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'link.tracker'
    _inherit = ['link.tracker', 'mail.thread', 'mail.activity.mixin']

    th_link_seeding_id = fields.Many2one('th.link.seeding', string="Link gốc")
    th_type = fields.Selection(selection=[('email_marketing', 'Email marketing'), ('link_seeding', 'Link seeding')])
    th_category = fields.Selection(selection=[('in_category', 'Trong danh mục'), ('out_of_category', 'Ngoài danh mục')])
    th_post_link_id = fields.One2many('th.post.link', 'link_tracker_id', 'Post link')
    th_partner_id = fields.Many2one('res.partner', 'Đối tác', readonly=True)
    th_image = fields.Binary(string="Ảnh sản phẩm")
    th_total_cost = fields.Float('Tổng chi phí', compute="_amount_all", store=True)

    @api.depends('th_post_link_id.th_pay')
    def _amount_all(self):
        total = 0
        link_posts = self.th_post_link_id
        for link_post in link_posts:
            if link_post.th_pay and link_post.state == "correct_request":
                total = total + float(link_post.th_pay)
        self.th_total_cost = total


class ThPostSeeding(models.Model):
    _name = "th.post.link"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char('Post link')
    link_tracker_id = fields.Many2one('link.tracker')
    th_note = fields.Text('Comment', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Nghiệm thu', readonly=1, tracking=True)
    th_seeding_acceptance_id = fields.Many2one('th.acceptance.seeding', 'Hệ số', tracking=True)
    th_pay = fields.Char('Chi phí', compute="compute_th_pay", tracking=True)
    state = fields.Selection(
        selection=[('pending', 'Chờ duyệt'), ('correct_request', 'Đúng yêu cầu'), ('wrong_request', 'Sai yêu cầu')],
        string='Trạng thái', tracking=True)

    @api.depends('th_seeding_acceptance_id')
    def compute_th_pay(self):
        for rec in self:
            if rec.th_seeding_acceptance_id:
                rec.th_pay = rec.th_seeding_acceptance_id.th_cost_factor
            else:
                rec.th_pay = False

    def write(self, values):
        state = values.get('state', False)
        th_seeding_acceptance_id = values.get('th_seeding_acceptance_id', False)
        if (state or th_seeding_acceptance_id) and self.partner_id.id != self.env.user.partner_id.id:
            # rec.partner_id = rec.env.user.partner_id.id
            values['partner_id'] = self.env.user.partner_id.id
        partner_id = values.get('partner_id', False)
        res = super(ThPostSeeding, self).write(values)
        for rec in self:
            if values and rec.link_tracker_id:
                model_main = rec.env['link.tracker'].search([('id', '=', rec.link_tracker_id.id)])
                mess_item = []
                if rec.name:
                    message = 'Link nghiệm thu: ' + rec.name
                    mess_item.append('<a href="%s" target="_blank">%s</a>' % (message, message))
                if partner_id:
                    th_partner = self.env['res.partner'].sudo().search([('id', '=', partner_id)])
                    mess_item.append("Nghiệm thu: " + th_partner.name)
                if th_seeding_acceptance_id:
                    th_seeding_acceptance = self.env['th.acceptance.seeding'].search([('id', '=', th_seeding_acceptance_id)])
                    mess_item.append("Hệ số: " + th_seeding_acceptance.th_coefficient)
                if state:
                    state_name = ''
                    if state == "pending":
                        state_name = 'Chờ duyệt'
                    elif state == "correct_request":
                        state_name = "Đúng yêu cầu"
                    else:
                        state_name = "Sai yêu cầu"
                    mess_item.append('Trạng thái: ' + state_name)

                if partner_id or state or th_seeding_acceptance_id:
                    body = _('<ul>%s</ul>') % ('\n'.join('<li>%s</li>' % name for name in mess_item))

                    model_main.message_post(
                        body=body,
                        message_type='comment')


        return res
