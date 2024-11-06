/** @odoo-module **/

import { ThProjectControlPanel } from "@th_project_itc/components/project_control_panel/project_control_panel";
import { registry } from "@web/core/registry";
import { graphView } from "@web/views/graph/graph_view";

const viewRegistry = registry.category("views");

export const thprojectGraphView = {...graphView, ControlPanel: ThProjectControlPanel};

viewRegistry.add("th_project_graph", thprojectGraphView);
