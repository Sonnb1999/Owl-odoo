/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { getBundle, loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { debounce } from "@web/core/utils/timing";

const { Component, onWillStart, onMounted, onWillUnmount, useRef, useState, markRaw } = owl;

const TEMPLATE_MODEL = "th.collaborator.contract.template";
// Ô nhỏ hơn ngưỡng này (px) coi như click nhầm, không tạo ô
const MIN_BOX_SIZE = 6;
const MAX_SCALE = 2;
// Cỡ chữ tự động giống phía server: 70% chiều cao ô, tối đa 11pt
const AUTO_FONT_RATIO = 0.7;
const AUTO_FONT_MAX = 11;

let nextLocalKey = 1;

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function round2(value) {
    return Math.round(value * 100) / 100;
}

/**
 * Màn hình vẽ ô đục lỗ lên PDF template hợp đồng.
 * Toạ độ ô được lưu theo hệ toạ độ PDF (point, gốc dưới-trái) để server vẽ chữ đúng vị trí.
 */
export class ThContractTemplateDesigner extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.containerRef = useRef("container");
        this.canvasRef = useRef("canvas");
        this.overlayRef = useRef("overlay");
        const params = this.props.action.params || {};
        this.templateId = params.template_id || (this.props.action.context || {}).active_id;
        this.state = useState({
            error: false,
            name: "",
            fieldOptions: [],
            boxes: [],
            pageCount: 0,
            currentPage: 1,
            pageWidth: 0,
            pageHeight: 0,
            viewportVersion: 0,
            selectedKey: false,
            draft: false,
            dirty: false,
            saving: false,
        });
        this.pdfDoc = null;
        this.viewport = null;
        this.renderTask = null;
        this.interaction = null;

        this.onWindowMouseMove = this.onWindowMouseMove.bind(this);
        this.onWindowMouseUp = this.onWindowMouseUp.bind(this);
        this.onWindowKeyDown = this.onWindowKeyDown.bind(this);
        // Render lại trang theo độ rộng mới khi đổi kích thước cửa sổ; toạ độ ô lưu theo PDF nên không bị lệch
        this.onWindowResize = debounce(() => this.pdfDoc && this.renderPage(), 200);

        onWillStart(() => this.loadData());
        onMounted(async () => {
            window.addEventListener("mousemove", this.onWindowMouseMove);
            window.addEventListener("mouseup", this.onWindowMouseUp);
            window.addEventListener("keydown", this.onWindowKeyDown);
            window.addEventListener("resize", this.onWindowResize);
            if (this.pdfDoc) {
                await this.renderPage();
            }
        });
        onWillUnmount(() => {
            window.removeEventListener("mousemove", this.onWindowMouseMove);
            window.removeEventListener("mouseup", this.onWindowMouseUp);
            window.removeEventListener("keydown", this.onWindowKeyDown);
            window.removeEventListener("resize", this.onWindowResize);
            if (this.renderTask) {
                this.renderTask.cancel();
            }
        });
    }

    // ------------------------------------------------------------------
    // Data
    // ------------------------------------------------------------------

    async fetchDesignerData() {
        return this.orm.call(TEMPLATE_MODEL, "th_get_designer_data", [[this.templateId]]);
    }

    setBoxesFromServer(boxes) {
        this.state.boxes = boxes.map((box) => Object.assign({}, box, { key: nextLocalKey++ }));
        this.state.selectedKey = false;
        this.state.dirty = false;
    }

    async loadData() {
        if (!this.templateId) {
            this.state.error = _t("Không xác định được template. Vui lòng mở lại từ form template hợp đồng.");
            return;
        }
        const data = await this.fetchDesignerData();
        this.state.name = data.name;
        this.state.fieldOptions = data.field_options;
        this.setBoxesFromServer(data.boxes);
        try {
            await loadBundle(await getBundle("web.pdf_js_lib"));
            this.pdfDoc = markRaw(await window.pdfjsLib.getDocument(data.pdf_url).promise);
            this.state.pageCount = this.pdfDoc.numPages;
        } catch (error) {
            this.state.error = _t("Không đọc được file PDF của template.");
        }
    }

    async save() {
        this.state.saving = true;
        try {
            const boxes = this.state.boxes.map((box) => ({
                id: box.id || false,
                page: box.page,
                x: round2(box.x),
                y: round2(box.y),
                width: round2(box.width),
                height: round2(box.height),
                font_size: box.font_size || 0,
                field_name: box.field_name || false,
            }));
            await this.orm.call(TEMPLATE_MODEL, "th_save_designer_boxes", [[this.templateId], boxes]);
            const data = await this.fetchDesignerData();
            this.setBoxesFromServer(data.boxes);
            const emptyCount = boxes.filter((box) => !box.field_name).length;
            this.notification.add(
                emptyCount
                    ? _t("Đã lưu. Có ô chưa chọn trường thông tin, ô đó sẽ bị bỏ qua khi đục lỗ.")
                    : _t("Đã lưu các ô đục lỗ."),
                { type: emptyCount ? "warning" : "success" }
            );
        } finally {
            this.state.saving = false;
        }
    }

    async onClickPreview() {
        if (this.state.dirty) {
            await this.save();
        }
        window.open(`/th_collaborator/contract/preview/template/${this.templateId}`, "_blank");
    }

    // ------------------------------------------------------------------
    // PDF rendering & coordinates
    // ------------------------------------------------------------------

    async renderPage() {
        const page = await this.pdfDoc.getPage(this.state.currentPage);
        const baseViewport = page.getViewport({ scale: 1 });
        const availableWidth = Math.max(this.containerRef.el.clientWidth - 48, 300);
        const scale = Math.min(availableWidth / baseViewport.width, MAX_SCALE);
        const viewport = page.getViewport({ scale });
        const canvas = this.canvasRef.el;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        if (this.renderTask) {
            this.renderTask.cancel();
        }
        this.renderTask = page.render({ canvasContext: canvas.getContext("2d"), viewport });
        try {
            await this.renderTask.promise;
        } catch (error) {
            // Chuyển trang nhanh sẽ huỷ lượt render cũ, không phải lỗi
            if (error && error.name === "RenderingCancelledException") {
                return;
            }
            throw error;
        }
        this.viewport = markRaw(viewport);
        this.state.pageWidth = viewport.width;
        this.state.pageHeight = viewport.height;
        this.state.viewportVersion++;
    }

    async changePage(delta) {
        const page = clamp(this.state.currentPage + delta, 1, this.state.pageCount);
        if (page === this.state.currentPage) {
            return;
        }
        this.state.currentPage = page;
        this.state.selectedKey = false;
        await this.renderPage();
    }

    async goToBox(box) {
        if (box.page !== this.state.currentPage) {
            this.state.currentPage = box.page;
            await this.renderPage();
        }
        this.state.selectedKey = box.key;
    }

    /** Toạ độ PDF -> khung hiển thị (px) trên canvas. */
    pdfToView(box) {
        const [x1, y1, x2, y2] = this.viewport.convertToViewportRectangle([
            box.x, box.y, box.x + box.width, box.y + box.height,
        ]);
        return {
            left: Math.min(x1, x2),
            top: Math.min(y1, y2),
            width: Math.abs(x2 - x1),
            height: Math.abs(y2 - y1),
        };
    }

    /** Khung hiển thị (px) -> toạ độ PDF, xử lý cả trang xoay/lệch gốc nhờ pdf.js. */
    viewToPdf(rect) {
        const [x1, y1] = this.viewport.convertToPdfPoint(rect.left, rect.top);
        const [x2, y2] = this.viewport.convertToPdfPoint(rect.left + rect.width, rect.top + rect.height);
        return {
            x: Math.min(x1, x2),
            y: Math.min(y1, y2),
            width: Math.abs(x2 - x1),
            height: Math.abs(y2 - y1),
        };
    }

    getPointer(ev) {
        const rect = this.overlayRef.el.getBoundingClientRect();
        return {
            x: clamp(ev.clientX - rect.left, 0, rect.width),
            y: clamp(ev.clientY - rect.top, 0, rect.height),
        };
    }

    // ------------------------------------------------------------------
    // Template helpers
    // ------------------------------------------------------------------

    get currentPageBoxes() {
        return this.state.boxes.filter((box) => box.page === this.state.currentPage);
    }

    get selectedBox() {
        return this.state.boxes.find((box) => box.key === this.state.selectedKey);
    }

    getFieldLabel(fieldName) {
        const option = this.state.fieldOptions.find((opt) => opt[0] === fieldName);
        return option ? option[1] : _t("Chưa chọn trường");
    }

    getBoxStyle(box) {
        // Đọc viewportVersion để vẽ lại ô khi đổi trang/tỉ lệ
        if (!this.state.viewportVersion || !this.viewport) {
            return "display: none;";
        }
        const rect = this.pdfToView(box);
        const pdfFontSize = box.font_size || Math.min(box.height * AUTO_FONT_RATIO, AUTO_FONT_MAX);
        return `left: ${rect.left}px; top: ${rect.top}px; width: ${rect.width}px; height: ${rect.height}px;` +
            ` font-size: ${pdfFontSize * this.viewport.scale}px;`;
    }

    getDraftStyle() {
        const draft = this.state.draft;
        return `left: ${draft.left}px; top: ${draft.top}px; width: ${draft.width}px; height: ${draft.height}px;`;
    }

    // ------------------------------------------------------------------
    // Interaction: vẽ / di chuyển / đổi kích thước ô
    // ------------------------------------------------------------------

    onOverlayMouseDown(ev) {
        if (ev.button !== 0 || !this.viewport) {
            return;
        }
        ev.preventDefault();
        const pointer = this.getPointer(ev);
        this.state.selectedKey = false;
        this.interaction = { mode: "draw", startX: pointer.x, startY: pointer.y };
        this.state.draft = { left: pointer.x, top: pointer.y, width: 0, height: 0 };
    }

    onBoxMouseDown(ev, box) {
        if (ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        const pointer = this.getPointer(ev);
        this.state.selectedKey = box.key;
        this.interaction = {
            mode: ev.target.dataset.handle === "resize" ? "resize" : "move",
            box,
            startX: pointer.x,
            startY: pointer.y,
            startRect: this.pdfToView(box),
        };
    }

    onWindowMouseMove(ev) {
        const interaction = this.interaction;
        if (!interaction) {
            return;
        }
        const pointer = this.getPointer(ev);
        if (interaction.mode === "draw") {
            this.state.draft = {
                left: Math.min(interaction.startX, pointer.x),
                top: Math.min(interaction.startY, pointer.y),
                width: Math.abs(pointer.x - interaction.startX),
                height: Math.abs(pointer.y - interaction.startY),
            };
            return;
        }
        const start = interaction.startRect;
        const dx = pointer.x - interaction.startX;
        const dy = pointer.y - interaction.startY;
        let rect;
        if (interaction.mode === "move") {
            rect = {
                left: clamp(start.left + dx, 0, this.state.pageWidth - start.width),
                top: clamp(start.top + dy, 0, this.state.pageHeight - start.height),
                width: start.width,
                height: start.height,
            };
        } else {
            rect = {
                left: start.left,
                top: start.top,
                width: clamp(start.width + dx, MIN_BOX_SIZE, this.state.pageWidth - start.left),
                height: clamp(start.height + dy, MIN_BOX_SIZE, this.state.pageHeight - start.top),
            };
        }
        // Lấy bản ghi reactive để OWL vẽ lại khi đổi toạ độ
        const box = this.state.boxes.find((item) => item.key === interaction.box.key);
        Object.assign(box, this.viewToPdf(rect));
        this.state.dirty = true;
    }

    onWindowMouseUp() {
        const interaction = this.interaction;
        this.interaction = null;
        if (!interaction || interaction.mode !== "draw") {
            return;
        }
        const draft = this.state.draft;
        this.state.draft = false;
        if (draft.width < MIN_BOX_SIZE || draft.height < MIN_BOX_SIZE) {
            return;
        }
        const box = Object.assign({
            key: nextLocalKey++,
            id: false,
            page: this.state.currentPage,
            font_size: 0,
            field_name: false,
        }, this.viewToPdf(draft));
        this.state.boxes.push(box);
        this.state.selectedKey = box.key;
        this.state.dirty = true;
    }

    onWindowKeyDown(ev) {
        const tag = ev.target && ev.target.tagName;
        if (ev.key !== "Delete" || ["INPUT", "SELECT", "TEXTAREA"].includes(tag)) {
            return;
        }
        this.deleteSelected();
    }

    // ------------------------------------------------------------------
    // Side panel
    // ------------------------------------------------------------------

    updateSelected(values) {
        const box = this.selectedBox;
        if (box) {
            Object.assign(box, values);
            this.state.dirty = true;
        }
    }

    onChangeField(ev) {
        this.updateSelected({ field_name: ev.target.value || false });
    }

    onChangeFontSize(ev) {
        const value = parseFloat(ev.target.value);
        this.updateSelected({ font_size: isNaN(value) || value < 0 ? 0 : value });
    }

    deleteSelected() {
        const index = this.state.boxes.findIndex((box) => box.key === this.state.selectedKey);
        if (index >= 0) {
            this.state.boxes.splice(index, 1);
            this.state.selectedKey = false;
            this.state.dirty = true;
        }
    }
}

ThContractTemplateDesigner.template = "th_collaborator.ContractTemplateDesigner";

registry.category("actions").add("th_collaborator.contract_template_designer", ThContractTemplateDesigner);
