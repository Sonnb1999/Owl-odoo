/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

const PROFILE_MODEL = "th.collaborator.profile";

/**
 * Registry nhà cung cấp chữ ký số kiểu "client" (ký trên trình duyệt qua plugin/USB Token).
 * Module nhà cung cấp đăng ký 1 object theo mã th_provider:
 *
 *   signProviderRegistry.add("ma_nha_cung_cap", {
 *       async sign(env, items, options) { ... },
 *   });
 *
 * - items: [{ profile_id, name, attachment_id, pdf_base64, page_count,
 *             sign_box: { page, x, y, width, height } }]  (toạ độ PDF, đơn vị point, gốc dưới-trái)
 * - options: tuỳ chọn hiển thị chung + tuỳ chọn riêng của nhà cung cấp (xem _get_client_sign_options)
 * - Trả về mảng cùng thứ tự items: { signed_pdf_base64, cert_base64 } hoặc { error }
 * - Lỗi chung của cả lô (chưa cài plugin, huỷ chọn chứng thư...) thì throw Error.
 */
export const signProviderRegistry = registry.category("th_collaborator_sign_providers");

/**
 * Client action ký số hợp đồng bên A cho nhiều CTV.
 * Gom hợp đồng theo cấu hình ký để mỗi nhóm chỉ nhập PIN 1 lần.
 */
async function signContractsAction(env, action) {
    const { orm, notification } = env.services;
    const profileIds = (action.params && action.params.profile_ids) || [];
    const { configs, items } = await orm.call(PROFILE_MODEL, "th_get_sign_payloads", [profileIds]);

    const itemsByConfig = {};
    for (const item of items) {
        (itemsByConfig[item.config_id] = itemsByConfig[item.config_id] || []).push(item);
    }

    const results = [];
    const errors = [];
    for (const [configId, groupItems] of Object.entries(itemsByConfig)) {
        const config = configs[configId];
        if (!signProviderRegistry.contains(config.provider)) {
            errors.push(_t("Chưa cài module tích hợp cho nhà cung cấp chữ ký số: ") + config.provider);
            continue;
        }
        let providerResults;
        try {
            providerResults = await signProviderRegistry.get(config.provider).sign(env, groupItems, config.options);
        } catch (error) {
            errors.push((error && error.message) || String(error));
            continue;
        }
        groupItems.forEach((item, index) => {
            const result = providerResults[index] || {};
            if (result.signed_pdf_base64) {
                results.push({
                    profile_id: item.profile_id,
                    attachment_id: item.attachment_id,
                    signed_pdf_base64: result.signed_pdf_base64,
                    cert_base64: result.cert_base64 || false,
                });
            } else {
                errors.push(`${item.name}: ${result.error || _t("Ký không thành công")}`);
            }
        });
    }

    if (results.length) {
        const saved = await orm.call(PROFILE_MODEL, "th_save_signed_contracts", [results]);
        if (saved.signed) {
            notification.add(_t("Đã ký số ") + saved.signed + _t(" hợp đồng."), { type: "success" });
        }
        if (saved.skipped.length) {
            errors.push(_t("Hợp đồng đã thay đổi trong lúc ký, vui lòng ký lại: ") + saved.skipped.join(", "));
        }
    }
    if (errors.length) {
        notification.add(errors.join(" | "), {
            title: _t("Ký số chưa hoàn tất"),
            type: "danger",
            sticky: true,
        });
    }
    // Đóng action để form/list gọi lại onClose và tải lại dữ liệu
    return { type: "ir.actions.act_window_close" };
}

registry.category("actions").add("th_collaborator.sign_contracts", signContractsAction);
