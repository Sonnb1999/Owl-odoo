async function fetchCookie(utmParams, fullUrl) {
    // const url_fetch = "https://samaff.eln.vn/curd/backlink";
    const url_fetch = "http://localhost:8017/curd/backlink";
    const code_session = sessionStorage.getItem("code");
    const date = new Date();

    const data = {
        link_tracker: fullUrl.split("?")[0],
        odoo_utm_params: utmParams,
        code: code_session != null ? code_session : "",
        referrer: document.referrer,
    };

    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    myHeaders.append("api-key", "admin");
    myHeaders.append("Access-Control-Allow-Headers", "*");


    const requestOptions = {
        method: "POST",
        headers: myHeaders,
        body: JSON.stringify(data), // Convert the data to JSON string
        redirect: "follow"
    };

    try {
        // const response = await fetch(url_fetch);
        const response = await fetch(url_fetch, requestOptions);
        const responseData = await response.json();
        let set_cookie = responseData.status_code == 200 ? responseData["detail"]['cookie'] : {};
        let interval_number = set_cookie["th_access_interval_number"] != undefined ? set_cookie["th_access_interval_number"] : 7;
        let interval_type = set_cookie["th_access_interval_type"] != undefined ? set_cookie["th_access_interval_type"] : "days";
        let code = responseData.status_code == 200 ? responseData["detail"]['code'] : false;
        if (sessionStorage.getItem("code") == null && code) {
            sessionStorage.setItem("code", code);
        }

        // 1 ngay = 86400
        let time_cookie_live = 86400;

        if (interval_type == "days") {
            time_cookie_live = interval_number * 24 * 60 * 60;
        } else if (interval_type == "hours") {
            time_cookie_live = interval_number * 60 * 60;
        } else if (interval_type == "minutes") {
            time_cookie_live = interval_number * 60;
        }

        const expires = new Date(
            Date.now() + time_cookie_live * 1000
        ).toUTCString();
        let utm_source = document.cookie.match(
            new RegExp("odoo_utm_source" + "=([^;]+)")
        );
        if (utm_source == null) {
            document.cookie = utmParams["utm_source"] != undefined ? "odoo_utm_source=" + utmParams["utm_source"] + "; expires=" + expires + "; path=/;" : "";
            document.cookie = utmParams["utm_campaign"] != undefined ? "odoo_utm_campaign=" + utmParams["utm_campaign"] + "; expires=" + expires + "; path=/;" : "";
            document.cookie = utmParams["utm_medium"] != undefined ? "odoo_utm_medium=" + utmParams["utm_medium"] + "; expires=" + expires + "; path=/;" : "";
        }
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        // Process the response if needed
        console.log(responseData);
    } catch (error) {
        console.error("Error fetching data:", error.message);
        // Handle errors as needd
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    let fullUrl = window.location.href;
    let utmParams = {};
    if (fullUrl.split("?")[1] != null) {
        const params = new URLSearchParams(fullUrl.split("?")[1]);
        for (const [key, val] of params) {
            if (key.startsWith("utm_")) {
                utmParams[key] = val;
            }
        }
    }

    if (Object.keys(utmParams).length) {
        await fetchCookie(utmParams, fullUrl);
    }
});
