/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { evalDomain } from "@web/views/utils";

patch(FormRenderer.prototype, "based_on_state_readonly_form", {
    setup() {
        this._super(...arguments);
        if (this.props.record.data.readonly_domain) {
            const readonly_domain = this.props.record.data.readonly_domain;
            const domain = evalDomain(readonly_domain, this.props.record.model.root.evalContext);
            if (domain) {
                this.props.record.mode = "readonly";
            }
        }
    },
})