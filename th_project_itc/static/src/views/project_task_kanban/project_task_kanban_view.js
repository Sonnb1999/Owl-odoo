/** @odoo-module */

import { registry } from "@web/core/registry";
import { kanbanView } from '@web/views/kanban/kanban_view';
import { ThProjectTaskKanbanModel } from "./project_task_kanban_model";
import { ThProjectTaskKanbanRenderer } from './project_task_kanban_renderer';
import { ThProjectControlPanel } from "../../components/project_control_panel/project_control_panel";

export const thprojectTaskKanbanView = {
    ...kanbanView,
    Model: ThProjectTaskKanbanModel,
    Renderer: ThProjectTaskKanbanRenderer,
    ControlPanel: ThProjectControlPanel,
};

registry.category('views').add('th_project_task_kanban', thprojectTaskKanbanView);
