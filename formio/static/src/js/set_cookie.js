async function th_set_cookie() {

    let fullUrl = window.location.href
    let utmParams = {}
    if (fullUrl.split("?")[1] != null) {
        const params = new URLSearchParams(fullUrl.split("?")[1]);
        for (const [key, val] of params) {
            if (key.startsWith("utm_")) {
                utmParams[key] = val;
            }
        }
    }

    if (Object.keys(utmParams).length) {
        await call_server(utmParams)
        await count_click(fullUrl, utmParams)
    }
    else {
        count_click_no_utm(fullUrl)
    }
}

    // window.addEventListener('message', (event) => {
    //     // Kiểm tra nguồn gốc của thông điệp
    //     if (event.origin === 'https://samdev.eln.vn') { // Đảm bảo nguồn gốc là đúng
    //         const receivedMessage = event.data;
    //         if formioSubmitDone
    //         // Xử lý thông điệp ở đây
    //         console.log('Received message from iframe:', receivedMessage);
    //     }
    // });


async function call_server(utmParams) {
    const url_fetch = 'https://samdev.eln.vn/api/check_cookie'
    const myHeaders = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, Content-Type, Access-Control-Allow-Origin"
    }
    let interval_number = 7
    let interval_type = 'days'

    let requestOptions = {
        mode: "cors",
        method: 'GET',
        headers: myHeaders,
        redirect: 'follow'
    };

    // let response = await fetch(url_fetch) ? await fetch(url_fetch) : undefined
    let response = await fetch(url_fetch)

    let data = response != undefined ? await response.json() : {};

    let set_cookie = data['results'] != undefined ? data['results'] : {}

    interval_number = set_cookie['th_access_interval_number'] != undefined ? set_cookie['th_access_interval_number'] : 7
    interval_type = set_cookie['th_access_interval_type'] != undefined ? set_cookie['th_access_interval_type'] : 'days'

    // 1 ngay = 86400
    let time_cookie_live = 86400

    if (interval_type == 'days') {
        time_cookie_live = interval_number * 24 * 60 * 60
    } else if (interval_type == 'hours') {
        time_cookie_live = interval_number * 60 * 60
    } else if (interval_type == 'minutes') {
        time_cookie_live = interval_number * 60
    }

    const expires = (new Date(Date.now() + time_cookie_live * 1000)).toUTCString();
    let utm_source = document.cookie.match(new RegExp('odoo_utm_source' + '=([^;]+)'))
    if (utm_source == null) {
        document.cookie = utmParams["utm_source"] != undefined ? "odoo_utm_source=" + utmParams['utm_source'] + "; expires=" + expires + "; path=/;" : ""
        document.cookie = utmParams["utm_campaign"] != undefined ? "odoo_utm_campaign=" + utmParams['utm_campaign'] + "; expires=" + expires + "; path=/;" : ""
        document.cookie = utmParams["utm_medium"] != undefined ? "odoo_utm_medium=" + utmParams['utm_medium'] + "; expires=" + expires + "; path=/;" : ""
    }
}

async function count_click(fullUrl, utmParams) {
    let code_session = sessionStorage.getItem('code')
    const url_server = 'https://samdev.eln.vn/api/backlink';
    let date = new Date()
    let data = {
        link_tracker: fullUrl.split("?")[0],
        odoo_utmParams: utmParams,
        code: code_session != null ? code_session  : '',
        date_start: date.toLocaleString()
    };

    let headers = new Headers({
        'Content-Type': 'application/json',
        'Authorization': '7fd3b7621caf03334a5036e6550adbc7b8311ecc'
    });

    await fetch(url_server, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            if (sessionStorage.getItem('code') == null)
            {
                sessionStorage.setItem("code", result['result']['code']);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

async function count_click_no_utm(fullUrl) {
    let referrer_link = document.referrer
    let code_session = sessionStorage.getItem('code')
    const url_server = 'https://samdev.eln.vn/api/backlink';
    let date = new Date()
    let data = {
        link_tracker: fullUrl.split("?")[0],
        code: code_session != null ? code_session : '',
        date_start: date.toLocaleString(),
        referrer_link: referrer_link
    };

    const headers = new Headers({
        'Content-Type': 'application/json',
        'Authorization': '7fd3b7621caf03334a5036e6550adbc7b8311ecc'
    });

    await fetch(url_server, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data)
    }).then(response => response.json())
        .then(result => {
            if (sessionStorage.getItem('code') == null) {
                sessionStorage.setItem("code", result['result']['code']);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

document.load = th_set_cookie()