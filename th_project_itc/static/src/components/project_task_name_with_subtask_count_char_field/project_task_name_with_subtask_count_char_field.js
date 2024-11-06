/** @odoo-module */

import { registry } from '@web/core/registry';
import { CharField } from '@web/views/fields/char/char_field';
import { formatChar } from '@web/views/fields/formatters';

class ThProjectTaskNameWithSubtaskCountCharField extends CharField {
    get formattedSubtaskCount() {
        return formatChar(this.props.record.data.allow_subtasks && this.props.record.data.child_text || '');
    }
}

ThProjectTaskNameWithSubtaskCountCharField.template = 'th_project_itc.ProjectTaskNameWithSubtaskCountCharField';

registry.category('fields').add('th_name_with_subtask_count', ThProjectTaskNameWithSubtaskCountCharField);
