from odoo import http
from odoo.http import request


class DownloadFormController(http.Controller):
    @http.route('/application_forms', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def download_forms(self, **kw):
        search_query = kw.get('search', '')
        domain = []
        if search_query:
            domain.append(('name', 'ilike', search_query))

        attachments = request.env['th.attachment'].search(domain)

        return request.render('th_portal_website.download_form_page', {
            'attachments': attachments,
            'search_query': search_query,
        })
