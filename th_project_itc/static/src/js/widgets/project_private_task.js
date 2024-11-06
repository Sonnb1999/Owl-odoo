/** @odoo-module alias=th_project_itc.th_project_private_task **/
"use strict";

import field_registry from 'web.field_registry';
import { FieldMany2One } from 'web.relational_fields';
import core from 'web.core';

const QWeb = core.qweb;

const ThProjectPrivateTask = FieldMany2One.extend({
    /**
     * @override
     * @private
     */
    _renderReadonly: function() {
        this._super.apply(this, arguments);
        if (!this.m2o_value) {
            this.$el.empty();
            this.$el.append(QWeb.render('th_project_itc.task.PrivateProjectName'));
            this.$el.addClass('pe-none');
        }
    },
});

field_registry.add('th_project_private_task', ThProjectPrivateTask);
