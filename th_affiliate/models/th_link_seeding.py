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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'th_product_aff_id'
    _check_company_auto = True

    th_url = fields.Char('Link mục tiêu', related='th_product_aff_id.th_link_product', store=True)
    th_request = fields.Html('Yêu cầu')
    medium_id = fields.Many2one('utm.medium', ondelete='set null', string='Kênh')
    th_image = fields.Binary(related='th_product_aff_id.th_image')
    campaign_id = fields.Many2one('utm.campaign', ondelete='set null', string='Chiến dịch', domain=lambda self: [('th_start_date', '<=', fields.Date.today()), ('th_end_date', '>=', fields.Date.today())], check_company=True)
    th_filename = fields.Char(compute='_compute_xml_filename', store=True)
    th_number_of_requests = fields.Integer('Số lượng yêu cầu', default=1)
    th_medium_ids = fields.Many2many('utm.medium', string='Kênh')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    th_aff_category_id = fields.Many2one('th.product.aff.category', 'Nhóm sản phẩm', required=True, check_company=True)
    th_product_aff_id = fields.Many2one('th.product.aff', 'Sản phẩm', required=True, domain="[('th_aff_category_id', '=?', th_aff_category_id),('state','=','deploy')]",  check_company=True)
    th_medium_ids = fields.Many2many('utm.medium', string='Kênh')

    @api.onchange('th_aff_category_id')
    def onchange_product_c(self):
        for rec in self:
            if not rec.th_aff_category_id:
                rec.th_product_aff_id = False

    @api.onchange('th_product_aff_id')
    def onchange_product(self):
        for rec in self:
            if not rec.th_aff_category_id:
                rec.th_aff_category_id = rec.th_product_aff_id.th_aff_category_id

    @api.depends('th_product_aff_id')
    def _compute_xml_filename(self):
        for rec in self:
            if rec.th_image:
                rec.th_filename = rec.th_product_aff_id.name
            else:
                rec.th_filename = False

    def action_create_link_tracker(self, user_id=None):
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
            if self.mapped('th_medium_ids'):
                for rec in self.mapped('th_medium_ids'):
                    if self.th_url:
                        value = self.env['link.tracker'].sudo().create({
                            'url': self.th_url,
                            'medium_id': rec.medium_id.id if rec.medium_id.id else False,
                            'campaign_id': self.campaign_id.id if self.campaign_id.id else False,
                            'th_link_seeding_id': self.id if self.id else False,
                            'th_type': 'link_seeding',
                            'source_id': utm_source_id.id if utm_source_id else False,
                            'th_aff_partner_id': contact_affiliate.id
                        })
                        return value
            else:
                if self.th_url:
                    value = self.env['link.tracker'].sudo().create({
                        'url': self.th_url,
                        'medium_id': self.medium_id.id if self.medium_id else False,
                        'campaign_id': self.campaign_id.id if self.campaign_id.id else False,
                        'th_link_seeding_id': self.id if self.id else False,
                        'th_type': 'link_seeding',
                        'source_id': utm_source_id.id if utm_source_id else False,
                        'th_aff_partner_id': contact_affiliate.id
                    })
                    return value

    # @api.model
    # def create(self, values):
    #     rec = super(ThLinkSeeding, self).create(values)
    #
    #     return rec
    #
    # def write(self, values):
    #     mediums = values.get('th_medium_ids', False)
    #     for rec in self:
    #         if mediums:
    #             pass
    #
    #     return super(ThLinkSeeding, self).write(values)
