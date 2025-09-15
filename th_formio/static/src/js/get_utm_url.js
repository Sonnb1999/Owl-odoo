function GetForm (name, id) {
    const f = document.createElement("iframe");
    let referrer = document.referrer
    let odoo_utm = th_get_cookie()
    f.setAttribute("src", name + "?referrer=" + odoo_utm);
    f.style.width = "100%";
    f.classList.add("formio_form_embed")

    let i = 0;
    let class_form = document.getElementsByClassName('formio_form_iframe_container')
    for (; i < class_form.length; i++){
        if(class_form[i].id == `formio_form_iframe_container_${id}`){
            let new_id = "formio_form_iframe_container_" + id + '_' + i;
            class_form[i].id = new_id
            let s = document.getElementById(new_id);
            if (s && !s.querySelector("iframe")) {
                s.appendChild(f);
            }
        }
    }
}


function th_get_cookie (){
    let r = window.document.referrer != "" ? window.document.referrer : window.location.origin;
    let regex = /(https?:\/\/.*?)\//g;
    let furl = regex.exec(r); r = furl ? furl[0] : r;
    let f = document.createElement("iframe");
    const url_string = new URLSearchParams(window.location.search);
    let utm_source, utm_campaign, utm_medium, utm_content, utm_term, utm_user, utm_account;

    if ((!url_string.has('utm_source') || url_string.get('utm_source') == '') && document.cookie.match(new RegExp('utm_source' + '=([^;]+)')) != null) {
        r += "&" + document.cookie.match(new RegExp('utm_source' + '=([^;]+)'))[0]; } else { r += url_string.get('utm_source') != null ? "&utm_source=" + url_string.get('utm_source') : "";
    }

    if ((!url_string.has('utm_campaign') || url_string.get('utm_campaign') == '') && document.cookie.match(new RegExp('utm_campaign' + '=([^;]+)')) != null) { r += "&" + document.cookie.match(new RegExp('utm_campaign' + '=([^;]+)'))[0]; }
    else { r += url_string.get('utm_campaign') != null ? "&utm_campaign=" + url_string.get('utm_campaign') : ""; }

    if ((!url_string.has('utm_medium') || url_string.get('utm_medium') == '') && document.cookie.match(new RegExp('utm_medium' + '=([^;]+)')) != null) { r += "&" + document.cookie.match(new RegExp('utm_medium' + '=([^;]+)'))[0]; }
    else { r += url_string.get('utm_medium') != null ? "&utm_medium=" + url_string.get('utm_medium') : ""; }

    if ((!url_string.has('utm_content') || url_string.get('utm_content') == '') && document.cookie.match(new RegExp('utm_content' + '=([^;]+)')) != null) { r += "&" + document.cookie.match(new RegExp('utm_content' + '=([^;]+)'))[0]; }
    else { r += url_string.get('utm_content') != null ? "&utm_content=" + url_string.get('utm_content') : ""; }

    if ((!url_string.has('utm_term') || url_string.get('utm_term') == '') && document.cookie.match(new RegExp('utm_term' + '=([^;]+)')) != null) { r += "&" + document.cookie.match(new RegExp('utm_term' + '=([^;]+)'))[0]; }
    else { r += url_string.get('utm_term') != null ? "&utm_term=" + url_string.get('utm_term') : ""; }

    r += "&full_url=" + encodeURIComponent(window.location.href);

    return r
}