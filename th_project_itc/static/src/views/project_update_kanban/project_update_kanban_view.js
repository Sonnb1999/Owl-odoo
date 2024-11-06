/** @odoo-module */

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { ThProjectUpdateKanbanController } from './project_update_kanban_controller';

export const thprojectUpdateKanbanView = {
    ...kanbanView,
    Controller: ThProjectUpdateKanbanController,
};

registry.category('views').add('th_project_update_kanban', thprojectUpdateKanbanView);
