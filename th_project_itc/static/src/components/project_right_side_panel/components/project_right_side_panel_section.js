/** @odoo-module */

const { Component } = owl;

export class ThProjectRightSidePanelSection extends Component { }

ThProjectRightSidePanelSection.props = {
    name: { type: String, optional: true },
    header: { type: Boolean, optional: true },
    show: Boolean,
    showData: { type: Boolean, optional: true },
    slots: {
        type: Object,
        shape: {
            default: Object, // Content is not optional
            header: { type: Object, optional: true },
            title: { type: Object, optional: true },
        },
    },
};
ThProjectRightSidePanelSection.defaultProps = {
    header: true,
    showData: true,
};

ThProjectRightSidePanelSection.template = 'th_project_itc.ProjectRightSidePanelSection';
