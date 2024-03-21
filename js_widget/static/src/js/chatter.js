/** @odoo-module **/
import {registerPatch} from '@mail/model/model_core';

registerPatch({
    name: 'Chatter',
    recordMethods: {
        async onClickShowMessageSystem() {
            await this.thread.cache.showMessageSystem();
        },
    },
});
