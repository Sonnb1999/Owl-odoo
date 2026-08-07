document.addEventListener("DOMContentLoaded", function () {
    check_cookie_vmc();
});

async function check_cookie_vmc() {
    let fullUrl = window.location.href
    let utmParams = {}
    if (fullUrl.split("?")[1] != null) {
        const params = new URLSearchParams(fullUrl.split("?")[1]);
        for (const [key, val] of params) {
            if (key.startsWith("utm_")) {
                utmParams[key] = val;
            }

            if (key.startsWith("id")) {
                utmParams[key] = val;
            }
        }
    }

    if (Object.keys(utmParams).length) {
        await vmc_call_server(utmParams)
    }
}

async function vmc_call_server(utmParams) {
    // 1 ngay = 86400
    let time_cookie_live = 604800
    let interval_number = 7
    let interval_type = 'days'

    const url_fetch = 'https://2p.sambala.net/api/check_cookie'
    const myHeaders = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, Content-Type, Access-Control-Allow-Origin"
    }

    let requestOptions = {
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    try {
        let response = await fetch(url_fetch)
        let data = await response.json();
        let set_cookie = data['results']

        interval_number = set_cookie['th_access_interval_number']
        interval_type = set_cookie['th_access_interval_type']


        if (interval_type == 'days') {
            time_cookie_live = interval_number * 24 * 60 * 60
        } else if (interval_type == 'hours') {
            time_cookie_live = interval_number * 60 * 60
        } else if (interval_type == 'minutes') {
            time_cookie_live = interval_number * 60
        }

    } catch (error) {
        time_cookie_live = interval_number * 24 * 60 * 60
    }
    const expires = (new Date(Date.now() + time_cookie_live * 1000)).toUTCString()
    let utm_source = document.cookie.match(new RegExp('odoo_utm_source' + '=([^;]+)'))
    if (utm_source == null) {
        document.cookie = utmParams["utm_source"] != undefined ? "odoo_utm_source=" + utmParams['utm_source'] + "; expires=" + expires + "; path=/;" : ""
        document.cookie = utmParams["utm_campaign"] != undefined ? "odoo_utm_campaign=" + utmParams['utm_campaign'] + "; expires=" + expires + "; path=/;" : ""
        document.cookie = utmParams["utm_medium"] != undefined ? "odoo_utm_medium=" + utmParams['utm_medium'] + "; expires=" + expires + "; path=/;" : ""
    }
}