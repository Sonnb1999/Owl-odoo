# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

import json
import logging

from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager

_logger = logging.getLogger(__name__)


class LinkTrackerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'get_link_seeding' in counters:
            domain = []
            values['get_link_seeding'] = (
                str(request.env['th.link.seeding'].sudo().search_count(domain)))

        if 'own_link_tracker' in counters:
            domain = [('th_partner_id.id', '=', request.env.user.partner_id.id)]
            values['own_link_tracker'] = (
                str(request.env['link.tracker'].sudo().search_count(domain)))

        return values

    # link seeding
    @http.route(['/my/seeding_partner'], type='http', auth="user", website=True)
    def seeding_partner(self, **kwargs):
        values = {
            'page_name': 'seeding_partner',
        }

        return request.render("th_link_tracker.th_seeding_partner", values)

    @http.route(['/my/get_link_seeding', '/my/get_link_seeding/page/<int:page>'], type='http', auth="user", website=True)
    def list_get_link_seeding(self, page=1, sortby='id', search='', search_in="All", **kwargs):
        domain = []
        th_link_seeding = request.env['th.link.seeding']
        total_links = th_link_seeding.sudo().search_count(domain)
        page_detail = pager(url='/my/get_link',
                            total=total_links,
                            page=page,
                            step=10)
        link_seeds = th_link_seeding.sudo().search(domain, limit=10, offset=page_detail['offset'], order='id desc')
        form_exist = request.env['link.tracker'].search([])

        values = {
            'link_seeds': link_seeds,
            'page_name': 'get_list_link_seeding',
            'pager': page_detail,
            # 'form_exist': form_exist
        }
        return request.render("th_link_tracker.th_list_get_link_seeding", values)

    @http.route(['/my/create_link_tracker/<model("th.link.seeding"):link_id>'], type='http', auth="user", website=True)
    def form_create_link_tracker(self, link_id, **kwargs):

        user_id = request.env.user.id
        contact_affiliate = request.env['res.partner'].sudo().search([('user_ids.id', '=', user_id)], limit=1)
        domain = [
            ('th_link_seeding_id', '=', link_id.id),
            ('th_partner_id', '=', contact_affiliate.id),
            ('campaign_id', '=', link_id.sudo().campaign_id.id),
            ('medium_id', '=', link_id.sudo().medium_id.id)
        ]

        link_exit = request.env['link.tracker'].sudo().search(domain)
        if not link_exit:
            create_link = request.env['th.link.seeding'].action_create_link_tracker(user_id, link_origin=link_id)
        value = link_exit if link_exit else create_link
        values = {'link_tracker': value, 'page_name': 'create_link'}
        return request.render("th_link_tracker.th_own_link_seeding", values)

    # link tracker
    @http.route(['/my/own_link_tracker', '/my/own_link_tracker/page/<int:page>'], type='http', auth="user", website=True)
    def list_own_link_tracker(self, page=1, sortby='id', search='', search_in="All", **kwargs):
        domain = [('th_partner_id.id', '=', request.env.user.partner_id.id)]
        th_link_tracker = request.env['link.tracker']
        total_links = th_link_tracker.sudo().search_count(domain)
        page_detail = pager(url='/my/get_link',
                            total=total_links,
                            page=page,
                            step=10)
        link_seeds = th_link_tracker.sudo().search(domain, limit=10, offset=page_detail['offset'], order='id desc')
        values = {
            'link_tracker': link_seeds,
            'page_name': 'own_links',
            'pager': page_detail,
        }
        return request.render("th_link_tracker.th_list_own_link_tracker", values)

    @http.route(['/my/info_link/<model("link.tracker"):link_tracker_id>'], type='http', auth="user", website=True)
    def form_info_link(self, link_tracker_id, **kwargs):
        values = {'link_tracker': link_tracker_id, 'page_name': 'own_link_info'}
        return request.render("th_link_tracker.th_own_link_seeding", values)

    # post link
    @http.route('/my/get_post_link/<model("link.tracker"):link_tracker_id>', type='http', auth="public", methods=['GET'], website=True)
    def get_post_link(self, link_tracker_id, **kwargs):
        post_link = link_tracker_id.th_post_link_id

        values = {
            'campaign_name': link_tracker_id.campaign_id.name,
            'count_click': len(link_tracker_id.link_click_ids),
            'post_link': post_link,
            'page_name': 'post_link_info',
        }

        return request.render("th_link_tracker.th_post_link", values)

    @http.route('/my/post_link', type='http', auth="public", methods=['POST'], csrf=False, website=True)
    def create_post_link(self, **kwargs):
        link_id = int(kwargs.get('id', False))
        post = request.env['link.tracker'].search([('id', '=', link_id)])
        link1 = kwargs.get('link1', False)
        link2 = kwargs.get('link2', False)
        link = [link1, link2]
        for rec in link:
            if rec:
                post_link = request.env['th.post.link'].create({
                    'link_tracker_id': link_id,
                    'name': rec,
                    'state': 'pending',
                })

        values = {
            'link_tracker': post,
            'page_name': 'own_link_info',
        }
        return request.render("th_link_tracker.th_own_link_seeding", values)

    # Sản phẩm ngoài danh mục
    @http.route('/my/link_outside', type='http', auth="public", methods=['POST'], csrf=False, website=True, save_session=False)
    def create_link_outside(self, **kwargs):
        user_id = request.env.user.id
        url_product = kwargs['own_url']
        contact_affiliate = request.env['res.partner'].sudo().search([('user_ids.id', '=', user_id)], limit=1)
        link_tracker = request.env['link.tracker']
        domain = [
            ('th_partner_id', '=', contact_affiliate.id),
            ('url', '=', url_product),
        ]
        link_exit = link_tracker.sudo().search(domain)
        if not link_exit:
            utm_source = request.env['utm.source'].sudo().search([('name', '=', contact_affiliate.th_affiliate_code)])
            if not utm_source and contact_affiliate:
                utm_source_id = utm_source.sudo().create({
                    'name': contact_affiliate.th_affiliate_code,
                })
            else:
                utm_source_id = utm_source.id

            request.env['link.tracker'].create({
                'th_partner_id': contact_affiliate.id,
                'url': url_product,
                'source_id': utm_source_id.id,
            })

        return self.list_own_link_tracker()
