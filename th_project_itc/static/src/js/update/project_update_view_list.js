/** @odoo-module **/

import ListController from 'web.ListController';
import ListRenderer from 'web.ListRenderer';
import ListView from 'web.ListView';
import viewRegistry from 'web.view_registry';
import ThProjectRightSidePanel from '@th_project_itc/js/right_panel/project_right_panel';
import {
    RightPanelControllerMixin,
    RightPanelRendererMixin,
    RightPanelViewMixin,
} from '@th_project_itc/js/right_panel/project_right_panel_mixin';

const ProjectUpdateListRenderer = ListRenderer.extend(RightPanelRendererMixin);

const ProjectUpdateListController = ListController.extend(RightPanelControllerMixin);

export const ProjectUpdateListView = ListView.extend(RightPanelViewMixin).extend({
    config: Object.assign({}, ListView.prototype.config, {
        Controller: ProjectUpdateListController,
        Renderer: ProjectUpdateListRenderer,
        RightSidePanel: ThProjectRightSidePanel,
    }),
});

viewRegistry.add('th_project_update_list', ProjectUpdateListView);
