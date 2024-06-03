from odoo import http
from odoo.http import request


class DownloadFormController(http.Controller):
    @http.route('/application_forms', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def download_forms(self, **kw):
        search_query = kw.get('search', '')
        domain = [('state', '=', 'accept'), ('th_type', '=', 'application_forms')]
        if search_query:
            domain.append(('name', 'ilike', search_query))

        attachments = request.env['th.attachment'].search(domain)

        return request.render('th_portal_website.download_form_page', {
            'name_page': 'CÁC MẪU ĐƠN',
            'action': '/application_forms',
            'attachments': attachments,
            'search_query': search_query,
        })

    @http.route('/regulations', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def regulations(self, **kw):
        search_query = kw.get('search', '')
        domain = [('state', '=', 'accept'), ('th_type', '=', 'regulations')]
        if search_query:
            domain.append(('name', 'ilike', search_query))

        attachments = request.env['th.attachment'].search(domain)

        return request.render('th_portal_website.download_form_page', {
            'name_page': 'QUY ĐỊNH - QUY CHẾ',
            'action': '/regulations',
            'attachments': attachments,
            'search_query': search_query,
        })

    @http.route('/image_page', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def regulations(self, **kw):
        search_query = kw.get('search', '')
        domain = [('state', '=', 'public')]
        if search_query:
            domain.append(('name', 'ilike', search_query))

        images = request.env['th.image.page'].search(domain)

        return request.render('th_portal_website.image_template', {
            'name_page': 'Ảnh',
            'action': '/image_page',
            'images': images,
            'search_query': search_query,
        })

    # @http.route('/introduce', auth='public', website=True, methods=['GET'], csrf=False)
    # def download_forms(self, **kw):
    #     search_query = kw.get('search', '')
    #     domain = [('state', '=', 'accept')]
    #     if search_query:
    #         domain.append(('name', 'ilike', search_query))
    #
    #     attachments = request.env['th.attachment'].search(domain)
    #
    #     return request.render('th_portal_website.download_form_page', {
    #         'attachments': attachments,
    #         'search_query': search_query,
    #     })
