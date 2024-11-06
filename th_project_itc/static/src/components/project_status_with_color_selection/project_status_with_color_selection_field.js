/** @odoo-module */

import { SelectionField } from '@web/views/fields/selection/selection_field';
import { registry } from '@web/core/registry';

import { STATUS_COLORS, STATUS_COLOR_PREFIX } from '../../utils/project_utils';

export class ThProjectStatusWithColorSelectionField extends SelectionField {
    setup() {
        super.setup();
        this.colorPrefix = STATUS_COLOR_PREFIX;
        this.colors = STATUS_COLORS;
    }

    get currentValue() {
        return this.props.value || this.options[0][0];
    }

    statusColor(value) {
        return this.colors[value] ? this.colorPrefix + this.colors[value] : "";
    }
}
ThProjectStatusWithColorSelectionField.template = 'th_project_itc.ProjectStatusWithColorSelectionField';

registry.category('fields').add('th_status_with_color', ThProjectStatusWithColorSelectionField);
