# -*- coding: utf-8 -*-

def migrate(cr, version):
    cr.execute("""
        UPDATE res_partner
        SET th_name_extra = name
        WHERE th_user_id = user_id
    """)
