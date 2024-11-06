/** @odoo-module */

import { registry } from '@web/core/registry';
import { Many2OneField } from '@web/views/fields/many2one/many2one_field';

export class ThProjectPrivateTaskMany2OneField extends Many2OneField { }
ThProjectPrivateTaskMany2OneField.template = 'th_project_itc.ProjectPrivateTaskMany2OneField';

registry.category('fields').add('th_project_private_task', ThProjectPrivateTaskMany2OneField);
