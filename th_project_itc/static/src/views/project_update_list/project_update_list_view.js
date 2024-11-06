/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ThProjectUpdateListController } from './project_update_list_controller';

export const thprojectUpdateListView = {
    ...listView,
    Controller: ThProjectUpdateListController,
};

registry.category('views').add('th_project_update_list', thprojectUpdateListView);
