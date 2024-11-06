/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from '@web/views/list/list_view';
import { ThProjectControlPanel } from "../../components/project_control_panel/project_control_panel";
import { ThProjectTaskListController } from './project_task_list_controller';

export const thprojectTaskListView = {
    ...listView,
    Controller: ThProjectTaskListController,
    ControlPanel: ThProjectControlPanel,
};

registry.category("views").add("th_project_task_list", thprojectTaskListView);
