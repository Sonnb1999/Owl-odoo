/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { clear, link } from '@mail/model/model_field_command';
const modelList = ["prm.lead", "pom.lead", "crm.lead", "ccs.lead"]

registerPatch({
    name: 'ThreadCache',
    recordMethods: {
         /**
         * @override
         */
         /**
         * @private
         * @param {Object} [param0={}]
         * @param {integer} [param0.limit=30]
         * @param {integer} [param0.maxId]
         * @param {integer} [param0.minId]
         * @returns {Message[]}
         * @throws {Error} when failed to load messages
         */
         async _loadMessages({limit = 30, maxId, minId} = {}) {
             // debugger
             this.update({isLoading: true});
             let messages;
             try {
                 messages = await this.messaging.models['Message'].performRpcMessageFetch(this.thread.fetchMessagesUrl, {
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
                 isLoading: false,
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
