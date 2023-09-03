function GetForm (name, id) {
    const f = document.createElement("iframe");
    const url_string = new URLSearchParams(window.location.search);
    let class_form = document.getElementsByClassName('formio_form_iframe_container')
    let i = 0
    let odoo_utm = th_get_cookie()

    f.setAttribute("src", name + odoo_utm);
    f.style.width = "100%";
    f.classList.add("formio_form_embed")

    for (; i < class_form.length; i++) {
        let new_id = "formio_form_iframe_container_" + id + '_' + i;
        class_form[i].id = new_id
        let s = document.getElementById(new_id);
        s.appendChild(f);
    }
}

function th_get_cookie (){

    let th_odoo_utm_source = document.cookie.match(new RegExp('odoo_utm_source' + '=([^;]+)'))
    let th_odoo_utm_campaign = document.cookie.match(new RegExp('odoo_utm_campaign' + '=([^;]+)'))
    let th_odoo_utm_medium = document.cookie.match(new RegExp('odoo_utm_medium' + '=([^;]+)'))

    let utm_campaign = th_odoo_utm_campaign != null ? "&utm_campaign=" + th_odoo_utm_campaign[0].split('=')[1] : ''
    let utm_source = th_odoo_utm_source != null ? "?utm_source=" + th_odoo_utm_source[0].split('=')[1] : ''
    let utm_medium = th_odoo_utm_medium != null ? "&utm_medium=" + th_odoo_utm_medium[0].split('=')[1] : ''
    let odoo_utm = utm_source + utm_campaign + utm_medium
    return odoo_utm
}