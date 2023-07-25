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

    th_title = fields.Char('Tiêu đề')
    th_url = fields.Char('Link mục tiêu', required=True)
    th_request = fields.Html('Yêu cầu')
    campaign_id = fields.Many2one('utm.campaign', ondelete='set null', string='Chiến dịch')
    medium_id = fields.Many2one('utm.medium', ondelete='set null', string='Kênh')
    th_cost = fields.Char('Giá mặc định', default=1500, required=True)
    th_image = fields.Binary(string="Ảnh sản phẩm")

    # source_id = fields.Many2one(ondelete='set null')

    @api.model
    @api.depends('th_url')
    def _get_title_from_th_url(self, th_url):
        try:
            head = requests.head(th_url, allow_redirects=True, timeout=5)
            if (int(head.headers.get('Content-Length', 0)) > URL_MAX_SIZE or 'text/html' not in head.headers.get('Content-Type', 'text/html')):
                return th_url
            # HTML parser can work with a part of page, so ask server to limit downloading to 50 KB
            page = requests.get(th_url, timeout=5, headers={"range": "bytes=0-50000"})
            p = html.fromstring(page.text.encode('utf-8'), parser=html.HTMLParser(encoding='utf-8'))
            th_title = p.find('.//title').text
        except:
            th_title = th_url

        return th_title

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

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [vals.copy() for vals in vals_list]
        for vals in vals_list:
            if 'th_url' not in vals:
                raise ValueError(_('Creating a Link Tracker without URL is not possible'))

            vals['th_url'] = tools.validate_url(vals['th_url'])

            if not vals.get('th_title'):
                vals['th_title'] = self._get_title_from_th_url(vals['th_url'])
        links = super(ThLinkSeeding, self).create(vals_list)
        return links

