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
    th_post_link_id = fields.One2many('th.post.link', 'link_tracker_id', 'Post link')
    th_partner_id = fields.Many2one('res.partner', 'Đối tác', readonly=True)


class ThLinkSeeding(models.Model):
    _name = "th.post.link"

    name = fields.Char('Post link')
    link_tracker_id = fields.Many2one('link.tracker')
    th_note = fields.Text('Comment')
    partner_id = fields.Many2one('res.partner', string='Nghiệm thu')
    th_pay = fields.Char('Thanh toán', tracking=True)
    state = fields.Selection(selection=[('pending', 'Chờ duyệt'), ('correct_request', 'Đúng yêu cầu'), ('wrong_request', 'Sai yêu cầu')], string='Trạng thái', tracking=True)
