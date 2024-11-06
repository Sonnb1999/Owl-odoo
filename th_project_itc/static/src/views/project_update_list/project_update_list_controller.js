/** @odoo-module */

import { ListController } from '@web/views/list/list_controller';
import { ThProjectRightSidePanel } from '../../components/project_right_side_panel/project_right_side_panel';

export class ThProjectUpdateListController extends ListController {
    get className() {
        return super.className + ' o_controller_with_rightpanel';
    }
}

ThProjectUpdateListController.components = {
    ...ListController.components,
    ThProjectRightSidePanel,
};
ThProjectUpdateListController.template = 'th_project_itc.ProjectUpdateListView';
