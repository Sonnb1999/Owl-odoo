/** @odoo-module **/

import ActivityView from '@mail/js/views/activity/activity_view';
import { ThProjectControlPanel } from '@th_project_itc/js/project_control_panel';
import viewRegistry from 'web.view_registry';

const ProjectActivityView = ActivityView.extend({
    config: Object.assign({}, ActivityView.prototype.config, {
        ControlPanel: ThProjectControlPanel,
    }),
});

viewRegistry.add('th_project_activity', ProjectActivityView);
