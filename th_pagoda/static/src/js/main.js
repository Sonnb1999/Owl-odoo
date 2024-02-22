/** @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import rpc from 'web.rpc';
import {patch} from "@web/core/utils/patch";

patch(ListController.prototype, 'th_pagoda.ListController', {
    setup() {
        this._super.apply(this, arguments);
        debugger
    },

    async onClickCarDemo() {
        await rpc.query({
            model: 'th.cars',
            method: 'th_action_create_demo',
            args: [[]],
        });
        return this.actionService.doAction({
            'type': 'ir.actions.client',
            'tag': 'reload',
        });

    },

    async onClickCompanyDemo() {
        await rpc.query({
            model: 'th.automobile.company',
            method: 'th_action_create_demo',
            args: [[]],
        });
        return this.actionService.doAction({
            'type': 'ir.actions.client',
            'tag': 'reload',
        });
    },

})