# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import random
import requests
import string

from lxml import html
from werkzeug import urls

from odoo import tools, models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

URL_MAX_SIZE = 10 * 1024 * 1024


class ThLinkSeeding(models.Model):
    _name = "th.link.seeding"

    th_url = fields.Char('Link mục tiêu', compute="_compute_url", store=True)
    th_request = fields.Html('Yêu cầu')
    medium_id = fields.Many2one('utm.medium', ondelete='set null', string='Kênh')
    th_image = fields.Binary(related='th_product_aff_id.th_image')
    campaign_id = fields.Many2one('utm.campaign', ondelete='set null', string='Chiến dịch', domain=lambda self: [('th_start_date', '<=', fields.Date.today()), ('th_end_date', '>=', fields.Date.today())])
    th_aff_category_id = fields.Many2one('th.product.aff.category', 'Nhóm sản phẩm', required=True)
    th_product_aff_id = fields.Many2one('th.product.aff', 'Sản phẩm', required=True, domain="[('th_aff_category_id', '=?', th_aff_category_id),('state','=','active')]")

    @api.depends('th_product_aff_id')
    def _compute_url(self):
        for rec in self:
            rec.th_url = rec.th_product_aff_id.th_link_product

    def action_create_link_tracker(self, user_id=None, link_origin=None):
        if not user_id:
            user_id = self.env.user.id
        if user_id:
            contact_affiliate = self.env['res.partner'].sudo().search([('user_ids.id', '=', user_id)], limit=1)
            utm_source_id = False
            utm_source = self.env['utm.source'].sudo().search([('name', '=', contact_affiliate.th_affiliate_code)])
            if not utm_source and contact_affiliate.th_affiliate_code:
                utm_source_id = utm_source.sudo().create({
                    'name': contact_affiliate.th_affiliate_code
                })
            if utm_source:
                utm_source_id = utm_source

            for rec in self or link_origin:
                if rec.th_url:
                    value = self.env['link.tracker'].sudo().create({
                        'url': rec.th_url,
                        'medium_id': rec.medium_id.id if rec.medium_id.id else False,
                        'campaign_id': rec.campaign_id.id if rec.campaign_id.id else False,
                        'th_link_seeding_id': rec.id if rec.id else False,
                        'th_type': 'link_seeding',
                        'source_id': utm_source_id.id if utm_source_id else False,
                        'th_partner_id': contact_affiliate.id
                    })
                    return value

