/** @odoo-module */

import { registry } from "@web/core/registry";
import { formView } from '@web/views/form/form_view';
import { ThFormRendererWithHtmlExpander } from './form_renderer_with_html_expander';

export const thformViewWithHtmlExpander = {
    ...formView,
    Renderer: ThFormRendererWithHtmlExpander,
};

registry.category('views').add('th_form_description_expander', thformViewWithHtmlExpander);
