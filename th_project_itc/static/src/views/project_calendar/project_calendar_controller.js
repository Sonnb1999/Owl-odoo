/** @odoo-module **/

import { CalendarController } from "@web/views/calendar/calendar_controller";

export class ThProjectCalendarController extends CalendarController {
    setup() {
        super.setup(...arguments);
        this.displayName += this.env._t(" - Tasks by Deadline");
    }
}
