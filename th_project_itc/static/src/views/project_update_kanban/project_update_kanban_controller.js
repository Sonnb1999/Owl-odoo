/** @odoo-module */

import { KanbanController } from '@web/views/kanban/kanban_controller';
import { ThProjectRightSidePanel } from '../../components/project_right_side_panel/project_right_side_panel';

export class ThProjectUpdateKanbanController extends KanbanController {
    get className() {
        return super.className + ' o_controller_with_rightpanel';
    }
}

ThProjectUpdateKanbanController.components = {
    ...KanbanController.components,
    ThProjectRightSidePanel,
};
ThProjectUpdateKanbanController.template = 'th_project_itc.ProjectUpdateKanbanView';
