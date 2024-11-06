/** @odoo-module **/

import { ThProjectControlPanel } from "@th_project_itc/components/project_control_panel/project_control_panel";
import { registry } from "@web/core/registry";
import { pivotView } from "@web/views/pivot/pivot_view";

const thprojectPivotView = {...pivotView, ControlPanel: ThProjectControlPanel};

registry.category("views").add("th_project_pivot", thprojectPivotView);
