/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2ManyTagsAvatarEmployeeField } from "@hr/views/fields/many2many_avatar_employee_field/many2many_avatar_employee_field";

export class ThMany2ManyTagsAvatarEmployeeField extends Many2ManyTagsAvatarEmployeeField {
    get tags() {
        return super.tags.map((tag) => ({
            ...tag,
            img: `/web/image/${this.props.relation}/${tag.resId}/avatar_1024`,
        }));
    }
}
registry.category("fields").add("th_many2many_avatar_employee", ThMany2ManyTagsAvatarEmployeeField);
