/** @odoo-module */

import { ConfirmationDialog } from '@web/core/confirmation_dialog/confirmation_dialog';

export class ThProjectStopRecurrenceConfirmationDialog extends ConfirmationDialog {
    _continueRecurrence() {
        if (this.props.continueRecurrence) {
            this.props.continueRecurrence();
        }
        this.props.close();
    }
}
ThProjectStopRecurrenceConfirmationDialog.template = 'th_project_itc.ProjectStopRecurrenceConfirmationDialog';
ThProjectStopRecurrenceConfirmationDialog.props.continueRecurrence = { type: Function, optional: true };
