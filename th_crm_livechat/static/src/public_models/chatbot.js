// /** @odoo-module **/
//
// import { registerPatch } from '@mail/model/model_core';
// import { attr, many, one } from '@mail/model/model_field';
//
// registerPatch({
//     name: 'Chatbot',
//     fields: {
//         isExpectingUserInput: one()
//     }
//
//
//     // fields: {
//     //     isExpectingUserInput: attr({
//     //         compute() {
//     //
//     //             if (!this.currentStep) {
//     //                 return clear();
//     //             }
//     //             return [
//     //                 'question_name',
//     //                 'question_phone',
//     //                 'question_email',
//     //                 'free_input_single',
//     //                 'free_input_multi',
//     //             ].includes(this.currentStep.data.chatbot_step_type);
//     //         },
//     //         default: false,
//     //     }),
//     // },
// });
//
