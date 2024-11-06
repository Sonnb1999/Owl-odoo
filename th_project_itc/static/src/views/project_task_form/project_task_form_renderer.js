/** @odoo-module */

import { ThFormRendererWithHtmlExpander } from "../form_with_html_expander/form_renderer_with_html_expander";

export class ThProjectTaskFormRenderer extends ThFormRendererWithHtmlExpander {
    get htmlFieldQuerySelector() {
        return '.o_field_html[name="description"]';
    }
}
