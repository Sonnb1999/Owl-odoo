/** @odoo-module **/

import core from 'web.core';
import {registerPatch} from '@mail/model/model_core';
import { clear, link } from '@mail/model/model_field_command';

registerPatch({
    name: 'Chatter',
    recordMethods: {
        async onClickShowMessageSystem({limit = 50, maxId, minId} = {}) {
             debugger
             this.update({isLoading: true});
             let messages;
             try {
                 messages = this.messaging.models['Message'].performRpcMessageFetch(this.thread.fetchMessagesUrl, {
                     ...this.thread.fetchMessagesParams,
                     limit,
                     'max_id': maxId,
                     'min_id': minId,
                     'th_param': {
                         'is_internal': true,
                     }
                 });
             } catch (e) {
                 if (this.exists()) {
                     this.update({
                         hasLoadingFailed: true,
                         isLoading: false,
                     });
                 }
                 throw e;
             }
             if (!this.exists()) {
                 return;
             }
             this.update({
                 rawFetchedMessages: link(messages),
                 hasLoadingFailed: false,
                 isLoaded: true,
                 isLoading: true,
             });
             if (!minId && messages.length < limit) {
                 this.update({isAllHistoryLoaded: true});
             }
             this.messaging.messagingBus.trigger('o-thread-cache-loaded-messages', {
                 fetchedMessages: messages,
                 threadCache: this,
             });
             return messages;
         },
    },
});
