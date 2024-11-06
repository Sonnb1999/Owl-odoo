/** @odoo-module */

import { registry } from "@web/core/registry";
import { thformViewWithHtmlExpander } from '../form_with_html_expander/form_view_with_html_expander';
import { ThProjectFormRenderer } from "./project_form_renderer";

export const thprojectFormView = {
    ...thformViewWithHtmlExpander,
    Renderer: ThProjectFormRenderer,
};

registry.category("views").add("th_project_form", thprojectFormView);
