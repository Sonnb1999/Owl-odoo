import json
import xmlrpc.client

from odoo import http, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request
from markupsafe import Markup
from urllib.parse import unquote
from odoo.addons.formio.controllers.main import FormioController
from odoo.addons.formio.controllers.utils import (
    generate_uuid4,
    log_form_submisssion,
    update_dict_allowed_keys,
    validate_csrf,
)

from odoo.addons.formio.models.formio_builder import STATE_CURRENT as BUILDER_STATE_CURRENT
from odoo.addons.formio.models.formio_form import (
    STATE_DRAFT as FORM_STATE_DRAFT,
    STATE_COMPLETE as FORM_STATE_COMPLETE,
)


class FormIOController(FormioController):

    ##############
    # Form Builder
    ##############

    @http.route('/formio/builder/<int:builder_id>', type='http', auth='user', website=True)
    def builder_root(self, builder_id, **kwargs):
        if not request.env.user.has_group('formio.group_formio_user'):
            # TODO Render template with message?
            return request.redirect("/")

        # TODO REMOVE (still needed or obsolete legacy?)
        # Needed to update language
        context = request.env.context.copy()
        context.update({'lang': request.env.user.lang})
        request.env.context = context

        builder = request.env['formio.builder'].browse(builder_id)
        languages = builder.languages
        lang_en = request.env.ref('base.lang_en')

        if lang_en.active and builder.language_en_enable and 'en_US' not in languages.mapped('code'):
            languages |= request.env.ref('base.lang_en')

        values = {
            'builder': builder,
            # 'languages' already injected in rendering somehow
            'builder_languages': languages,
            'formio_css_assets': builder.formio_css_assets,
            'formio_js_assets': builder.formio_js_assets,
            'extra_assets': builder.extra_asset_ids,
            # uuid is used to disable assets (js, css) caching by hrefs
            'uuid': generate_uuid4()
        }
        return request.render('formio.formio_builder_embed', values)

    @http.route('/formio/builder/<model("formio.builder"):builder>/save', type='http', auth="user", methods=['POST'], csrf=False)
    def builder_save(self, builder):
        self.validate_csrf()
        if not request.env.user.has_group('formio.group_formio_user'):
            return

        post = request.get_json_data()
        if 'builder_id' not in post or int(post['builder_id']) != builder.id:
            return

        schema = json.dumps(post['schema'])
        builder.write({'schema': schema})

    @http.route('/formio/builder/<int:builder_id>/config', type='json', auth='user', website=True)
    def builder_config(self, builder_id, **kwargs):
        if not request.env.user.has_group('formio.group_formio_user'):
            return
        builder = request.env['formio.builder'].browse(builder_id)
        res = {'schema': {}, 'options': {}}

        url_form = request.httprequest.host_url
        if builder:
            if builder.schema:
                res['schema'] = json.loads(builder.schema)
            res['options'] = builder._get_js_options()
            res['options']['builder'] = {
                'basic': False,
                'advanced': False,
                'data': False,
                'customBasicInfor': {
                    'title': 'Thông tin cơ bản',
                    'default': True,
                    'weight': 0,
                    'components': {
                        "key": "api",
                        "ignore": False,
                        'name': {
                            'title': 'Họ và Tên',
                            'key': 'name',
                            'icon': 'terminal',
                            'schema': {
                                'label': 'Họ và Tên',
                                'type': 'textfield',
                                'key': 'name',
                                'input': True,
                                "errors": {
                                    "required": "{{ field }} không được để trống.",
                                },
                                "validate": {
                                    "required": True
                                },
                            }
                        },
                        'custom_email': {
                            'title': 'Email',
                            'key': 'email',
                            'icon': 'at',
                            'schema': {
                                'label': 'Email',
                                'type': 'email',
                                'key': 'email',
                                'input': True,
                                'errors': {
                                    "required": "{{ field }} không được để trống.",
                                    "invalid_email": "{{ field }} chưa đúng. {{ field }} giống như abcd@xyz.com"
                                },
                                'validate': {
                                    "required": True
                                },
                            }
                        },
                        'cellPhone': {
                            'title': 'Số điện thoại',
                            'key': 'phone',
                            'icon': 'phone-square',
                            'inputMask': "",
                            'schema': {
                                'label': 'Số điện thoại',
                                'type': 'phoneNumber',
                                'key': 'phone',
                                'input': True,
                                'inputMask': "",
                                'errors': {
                                    'required': "{{ field }} không được để trống.",
                                    'mask': "{{ field }} chưa đúng.",
                                    'pattern': "Số điện thoại không hợp lệ. Vui lòng nhập đúng định dạng và tránh số ảo."
                                },
                                'validate': {
                                    "required": True,
                                    "pattern": "^(01|02|03|04|05|06|07|08|09)[0-9]{8,9}$",
                                    "customMessage": "Số điện thoại không hợp lệ. Vui lòng kiểm tra lại định dạng và tránh dãy số tăng/giảm liên tiếp.",
                                    "custom": "valid = (!input || (/^[0-9]{10,11}$/.test(input) && /^(01|02|03|04|05|06|07|08|09)/.test(input) && !/^(0123456789|1234567890|9876543210|0987654321)/.test(input.slice(0,10))));"
                                },
                            }
                        },
                        'custom_panel': {
                            'title': 'Khung form',
                            'key': 'panel',
                            "label": "Panel",
                            'icon': 'list-alt',
                            'schema': {
                                "title": "Đăng ký nhận tư vấn",
                                "theme": "success",
                                "type": "panel",
                                'key': 'panel',
                                'input': False,
                            }
                        },
                        'th_textarea': {
                            'title': 'Mô tả',
                            'key': 'th_textArea',
                            'icon': 'fa-font',
                            'inputMask': "",
                            'schema': {
                                "label": "Mô tả",
                                "applyMaskOn": "change",
                                "autoExpand": False,
                                "tableView": True,
                                "key": "th_textArea",
                                "type": "textarea",
                                "input": True
                            },
                        },
                        'custom_button': {
                            'title': 'Nút đăng ký',
                            'key': 'submit',
                            'icon': 'stop',
                            'schema': {
                                "label": "Đăng ký",
                                "customClass": "mt-2 th_disabled",
                                "type": "button",
                                'key': 'submit',
                                'input': True,
                                'saveOnEnter': False,
                                'disableOnInvalid': True,
                            }
                        },
                        'source_group': {
                            'title': 'Nhóm nguồn',
                            'key': 'source_group',
                            'icon': 'terminal',
                            'inputMask': "",
                            'schema': {
                                'label': 'Nhóm nguồn',
                                'type': 'textfield',
                                'key': 'source_group',
                                'input': True,
                                'inputMask': "",
                                'errors': {
                                    'required': "{{ field }} không được để trống.",
                                    'mask': "{{ field }} chưa đúng."
                                },
                                'validate': {
                                    "required": True
                                },
                            }
                        },
                    },
                },

                'customCRM': {
                    'title': 'CRM',
                    'weight': 1,
                    'components': {
                        'university': {
                            'title': 'Trường học(Ẩn trên form)',
                            'key': 'university',
                            'icon': 'fa-graduation-cap',
                            'schema': {
                                'label': 'Trường học',
                                'type': 'select',
                                'key': 'university',
                                'input': True,
                                'dataSrc': "url",
                                'template': "<span>{{ item.name }}</span>",
                                'conditional': {
                                    'show': True,
                                    'when': 'submit'
                                },
                                'data': {
                                    'url': url_form + "get_universities",
                                    'headers': [
                                        {
                                            "key": "",
                                            "value": ""
                                        }
                                    ]
                                },
                            }
                        },
                        'major': {
                            'title': 'Ngành học(Tìm theo trường)',
                            'key': 'majors',
                            'icon': 'paste',
                            'schema': {
                                'label': 'Ngành học',
                                'type': 'select',
                                'key': 'majors',
                                'input': True,
                                'dataSrc': "url",
                                'refreshOn': "university",
                                'template': "<span>{{ item.name }}</span>",
                                'clearOnRefresh': True,
                                'noRefreshOnScroll': False,
                                'ignoreCache': True,
                                'multiple': False,
                                'data': {
                                    'url': url_form + "get_majors?university={{row.university.university_code}}",
                                    'headers': [
                                        {
                                            "key": "",
                                            "value": ""
                                        }
                                    ]
                                },
                            }
                        },

                        'university01': {
                            'title': 'Trường học(Tất cả các trường)',
                            'key': 'university',
                            'icon': 'fa-graduation-cap',
                            'schema': {
                                'label': 'Trường học',
                                'type': 'select',
                                'key': 'university',
                                'input': True,
                                'dataSrc': "url",
                                'template': "<span>{{ item.name }}</span>",
                                'data': {
                                    'url': url_form + "get_universities",
                                    'headers': [
                                        {
                                            "key": "",
                                            "value": ""
                                        }
                                    ]
                                },
                            }
                        },
                        'major01': {
                            'title': 'Ngành học(Tất cả các ngành)',
                            'key': 'majors',
                            'icon': 'paste',
                            'schema': {
                                'label': 'Ngành học',
                                'type': 'select',
                                'key': 'majors',
                                'input': True,
                                'dataSrc': "url",
                                'template': "<span>{{ item.name }}</span>",
                                'clearOnRefresh': True,
                                'noRefreshOnScroll': False,
                                'ignoreCache': True,
                                'multiple': True,
                                'data': {
                                    'url': url_form + "get_majors",
                                    'headers': [
                                        {
                                            "key": "",
                                            "value": ""
                                        }
                                    ]
                                },
                            }
                        },
                    }
                },

                'customAPM': {
                    'title': 'APM',
                    'weight': 2,
                    'components': {
                        'apm_ownership_unit': {
                            'title': 'Đơn vị sở hữu',
                            'key': 'apm_ownership_unit',
                            'icon': 'fa-graduation-cap',
                            'schema': {
                                'label': 'Đơn vị sở hữu',
                                'type': 'select',
                                'key': 'apm_ownership_unit',
                                'input': True,
                                'dataSrc': "url",
                                'template': "<span>{{ item.name }}</span>",
                                'validate': {
                                    "required": True
                                },
                                'data': {
                                    'url': url_form + "get_apm_ownership_units",
                                    'headers': [
                                        {
                                            "key": "",
                                            "value": ""
                                        }
                                    ]
                                },
                            }
                        },
                    }
                },

                'customPRM': {
                    'title': 'PRM',
                    'weight': 3,
                    'components': {
                        'cooperation_program': {
                            'title': 'Chương trình hợp tác',
                            'key': 'cooperation_program',
                            'icon': 'tasks',
                            'inputMask': "",
                            'schema': {
                                'label': 'Chương trình hợp tác',
                                'type': 'select',
                                'key': 'cooperation_program',
                                'input': True,
                            }
                        },
                    }
                },

                'customBasic': {
                    'title': 'Cơ bản',
                    'weight': 10,
                    'components': {
                        'textfield': True,
                        'textarea': True,
                        'email': True,
                        'phoneNumber': True,
                        'select': True,
                        'panel': True,
                        'button': True,
                    }
                },
                'layout': {
                    'components': {
                        'table': False
                    }
                }
            }
            res['locales'] = builder._get_form_js_locales()
            res['params'] = builder._get_js_params()
            res['csrf_token'] = request.csrf_token()
            cus_form = request.env['th.custom.view.formio'].search([('state', '=', True)])

            # Lấy trường cẩn ẩn
            th_fields = []
            for rec_hide in cus_form:
                if rec_hide.th_key not in th_fields:
                    th_fields.append(rec_hide.th_key)

            # lấy những thông tin ẩn
            for th_field in th_fields:
                res['options']['editForm'][th_field] = []
                th_values = cus_form.filtered(lambda l: l.th_key == th_field)
                for rec_v in th_values:
                    res['options']['editForm'][th_field] += [{'key': rec_v.th_value, 'ignore': True}]
            # {
            #     'editForm': {
            #         'Họ và Tên': [
            #             {
            #                 "key": "validation",
            #                 "components": [
            #                     {"key": "unique", "ignore": True},
            #                     {'key': 'unique', 'defaultValue': True},
            #                 ]
            #             },
            #         ]
            #     }
            # }

            if request.env['res.users'].search([('id', '=', request.uid)]).lang == 'vi_VN':
                langs = request.env['th.translate'].search([]).filtered(
                    lambda l: l.lang_id and l.lang_id.code == 'vi_VN')
                if langs:
                    res['options']['i18n'] = {'vi-VN': {}}
                    res['options']['language'] = 'vi-VN'
                for lang in langs:
                    res['options']['i18n']['vi-VN'].update({lang.th_key: lang.th_value})
                res['locales'].update({'vi-VN': 'vi'})
        return request.make_json_response(res)
