/** @odoo-module **/
const {xml, Component} = owl;
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {UrlField} from "@web/views/fields/url";
import {registry} from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";

class TreeUrlField extends UrlField {
    setup() {
        super.setup();
        debugger
        useInputField({getValue: () => this.props.value || ""});
    }

    get formattedHref() {
        debugger
        let value = "";
        if (typeof this.props.value === "string") {
            const shouldaddPrefix = !(
                this.props.websitePath ||
                this.props.value.includes("://") ||
                /^\//.test(this.props.value)
            );
            value = shouldaddPrefix ? `http://${this.props.value}` : this.props.value;
        }
        return value;
    }
}

TreeUrlField.props = {
    ...standardFieldProps,
    options: {type: Object, optional: true}
}
TreeUrlField.extractProps = ({attrs}) => {
    return {options: attrs.options}
}


registry.category("fields").add("tree.tree_url", TreeUrlField);
