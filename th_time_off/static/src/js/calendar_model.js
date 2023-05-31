/** @odoo-module **/
import {TimeOffCalendarModel} from "@hr_holidays/views/calendar/calendar_model";
import {patch} from "@web/core/utils/patch";
import {deserializeDateTime, serializeDate, serializeDateTime} from "@web/core/l10n/dates";

patch(TimeOffCalendarModel.prototype, 'th_time_off.calendar_model', {
    /**
     * When choose day in calendar
     * change default date to = 8:00
     * if saturday default date from = 12:00
     * */

    makeContextDefaults(record) {
        const context = this._super(...arguments)
        if ('default_date_from' in context && 'default_date_to' in context) {
            let th_default_date_from = new Date(context.default_date_from).getDay()
            let th_default_date_to = new Date(context.default_date_to).getDay()

            context['default_date_from'] = serializeDateTime(deserializeDateTime(context['default_date_from']).set({
                hours: 8,
                minute: 0
            }));

            if (th_default_date_from == 6 && th_default_date_to == 6) {

                context['default_date_to'] = serializeDateTime(deserializeDateTime(context['default_date_from']).set({
                    hours: 12,
                    minute: 0
                }));

            } else {
                context['default_date_to'] = serializeDateTime(deserializeDateTime(context['default_date_from']).set({
                    hours: 17,
                    minute: 0
                }));
            }

        }
        return context;
    }
})