/** @odoo-module **/

import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { signProviderRegistry } from "@th_collaborator/js/th_contract_sign_action";

// SDK chỉ nạp khi ký (~150KB), không đưa vào bundle backend
const VNPT_PLUGIN_URL = "/th_collaborator_sign_vnpt/static/lib/vnpt_plugin/vnpt-plugin.js";

// Mã lỗi trả về của signArrDataAdvanced (theo trang mẫu của VNPT)
const VNPT_SIGN_ERRORS = {
    1: _t("Dữ liệu đầu vào không đúng định dạng"),
    2: _t("Không lấy được thông tin chứng thư số"),
    3: _t("Có lỗi trong quá trình ký số"),
    4: _t("Chứng thư số không có khóa bí mật"),
    5: _t("Lỗi không xác định"),
    6: _t("Không tìm thấy tham số số trang cần ký"),
    7: _t("Trang đặt chữ ký không tồn tại"),
    9: _t("Không tìm thấy id của thẻ ký số"),
    10: _t("Dữ liệu ký đã chứa một hoặc nhiều chữ ký không hợp lệ"),
    11: _t("Người dùng hủy bỏ"),
    13: _t("Dữ liệu ký rỗng"),
};

// Kiểu hiển thị chung -> SigType của VNPT (0: chỉ mô tả, 1: mô tả + tên, 2: mô tả + ảnh, 3: chỉ ảnh)
const VNPT_SIG_TYPES = {
    description: 0,
    description_name: 1,
    description_image: 2,
    image: 3,
    invisible: 0,
};

function formatSigningTime(date) {
    const pad = (value) => String(value).padStart(2, "0");
    return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())} ` +
        `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()}`;
}

/** Chuyển cấu hình chung + vị trí ô ký sang tham số PdfSigner của VNPT-CA Plugin. */
function buildPdfSigner(item, options, certSerial) {
    const box = item.sign_box;
    const signingTime = formatSigningTime(new Date());
    const withImage = ["description_image", "image"].includes(options.appearance_type);
    const allPages = Array.from({ length: item.page_count }, (_value, index) => index + 1);
    return {
        page: box.page,
        llx: box.x,
        lly: box.y,
        urx: box.x + box.width,
        ury: box.y + box.height,
        SigTextSize: options.text_size,
        Signer: null,
        SignerPosition: null,
        SigningTime: signingTime,
        Description: options.description ? options.description.replace("{thoi_gian}", signingTime) : null,
        OnlyDescription: Boolean(options.description),
        ImageBase64: withImage ? options.image_base64 : null,
        ValidationOption: false,
        SigColorRGB: options.text_color || null,
        SetImageBackground: false,
        PagesArray: options.initial_all_pages ? allPages : null,
        CertificateSerial: certSerial || null,
        TsaUrl: options.tsa_url || null,
        TsaUsername: null,
        TsaPassword: null,
        AdvancedCustom: false,
        SigType: VNPT_SIG_TYPES[options.appearance_type] || 0,
        IsEncyptFile: false,
        EncryptPassword: null,
        SigVisible: options.appearance_type !== "invisible",
        SigSignerVisible: options.signer_visible,
        SigEmailVisible: options.email_visible,
        SigPositionVisible: options.position_visible,
        SigSigningTimeVisible: options.signing_time_visible,
    };
}

/** Kết quả signArrDataAdvanced: 1 object (lỗi chung) hoặc mảng chuỗi JSON (mỗi file 1 kết quả). */
function parseSignResults(raw, count) {
    const parsed = JSON.parse(raw);
    const results = Array.isArray(parsed)
        ? parsed.map((result) => (typeof result === "string" ? JSON.parse(result) : result))
        : [parsed];
    if (results.length === 1 && count > 1) {
        return Array(count).fill(results[0]);
    }
    return results;
}

async function getReadyPlugin(licenseKey) {
    if (!licenseKey) {
        throw new Error(_t("Chưa khai báo license key VNPT-CA Plugin trong Cấu hình ký số."));
    }
    await loadJS(VNPT_PLUGIN_URL);
    const plugin = window.vnpt_plugin;
    let status = false;
    try {
        status = await plugin.checkPlugin();
    } catch (_error) {
        status = false;
    }
    if (status !== "1") {
        throw new Error(_t("VNPT-CA Plugin chưa được cài đặt hoặc chưa được bật trên máy tính này."));
    }
    await plugin.setLicenseKey(licenseKey);
    return plugin;
}

signProviderRegistry.add("vnpt_plugin", {
    async sign(env, items, options) {
        const plugin = await getReadyPlugin(options.vnpt_license_key);
        // Chọn chứng thư 1 lần cho cả lô: lưu vết người ký và ký mọi file bằng cùng 1 chứng thư
        const certRaw = await plugin.getCertInfo(null, true, "");
        if (!certRaw) {
            throw new Error(_t("Không lấy được thông tin chứng thư số. Vui lòng kiểm tra USB Token."));
        }
        const cert = JSON.parse(certRaw);
        const arrData = items.map((item) => JSON.stringify({
            data: item.pdf_base64,
            type: "pdf",
            sigOptions: JSON.stringify(buildPdfSigner(item, options, cert.serial)),
        }));
        // Trên macOS VNPT khuyến nghị xoá cache PIN sau mỗi lần ký
        const clearPinCache = plugin.getOsName() === "MAC";
        const raw = await plugin.signArrDataAdvanced(arrData, cert.serial || "", clearPinCache, null, false);
        return parseSignResults(raw, items.length).map((result) => {
            if (result.code === 0 && result.data) {
                return { signed_pdf_base64: result.data, cert_base64: cert.base64 };
            }
            return { error: VNPT_SIGN_ERRORS[result.code] || _t("Lỗi không xác định") };
        });
    },
});
