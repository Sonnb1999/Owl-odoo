/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { ThProjectCalendarController } from "@th_project_itc/views/project_calendar/project_calendar_controller";
import { ThProjectControlPanel } from "@th_project_itc/components/project_control_panel/project_control_panel";

export const thprojectCalendarView = {
    ...calendarView,
    Controller: ThProjectCalendarController,
    ControlPanel: ThProjectControlPanel,
};
registry.category("views").add("th_project_calendar", thprojectCalendarView);
