/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { evalDomain } from "@web/views/utils";
import { onRendered } from "@odoo/owl";

const PatchFormObjectReadonly = {
    setup() {
        this._super(...arguments);
        onRendered(() => {
            if (this.model.root.data.readonly_domain){
                const readonly_domain = this.model.root.data.readonly_domain;
                const domain = evalDomain(readonly_domain, this.model.root.evalContext);
                if (domain) {
                    this.model.root.mode = "readonly";
                }else {
                    this.model.root.mode = "edit";
                }
            }
            this.env.config.setDisplayName(this.displayName());
        });
    },
};
patch(FormController.prototype, "form_readonly_patch", PatchFormObjectReadonly);