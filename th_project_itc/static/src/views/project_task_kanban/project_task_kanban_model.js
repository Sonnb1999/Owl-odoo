/** @odoo-module */

import { KanbanModel } from "@web/views/kanban/kanban_model";

import { ThProjectTaskKanbanDynamicGroupList } from "./project_task_kanban_dynamic_group_list";
import { ThProjectTaskRecord } from './project_task_kanban_record';

export class ThProjectTaskKanbanGroup extends KanbanModel.Group {
    get isPersonalStageGroup() {
        return !!this.groupByField && this.groupByField.name === 'personal_stage_type_ids';
    }

    async delete() {
        if (this.isPersonalStageGroup) {
            this.deleted = true;
            return await this.model.orm.call(this.resModel, 'remove_personal_stage', [this.resId]);
        } else {
            return await super.delete();
        }
    }
}

export class ThProjectTaskKanbanModel extends KanbanModel { }

ThProjectTaskKanbanModel.DynamicGroupList = ThProjectTaskKanbanDynamicGroupList;
ThProjectTaskKanbanModel.Group = ThProjectTaskKanbanGroup;
ThProjectTaskKanbanModel.Record = ThProjectTaskRecord;
