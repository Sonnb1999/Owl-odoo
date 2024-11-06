/** @odoo-module */

import { registry } from "@web/core/registry";
import { thformViewWithHtmlExpander } from '../form_with_html_expander/form_view_with_html_expander';
import { ThProjectTaskFormController } from './project_task_form_controller';
import { ThProjectTaskFormRenderer } from "./project_task_form_renderer";

export const thprojectTaskFormView = {
    ...thformViewWithHtmlExpander,
    Controller: ThProjectTaskFormController,
    Renderer: ThProjectTaskFormRenderer,
};

registry.category("views").add("th_project_task_form", thprojectTaskFormView);
