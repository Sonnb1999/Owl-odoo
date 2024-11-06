/** @odoo-module */

const { Component } = owl;

export class ThProjectProfitability extends Component {
    get revenues() {
        return this.props.data.revenues;
    }

    get costs() {
        return this.props.data.costs;
    }

    get margin() {
        const invoiced_billed = this.revenues.total.invoiced + this.costs.total.billed;
        const to_invoice_to_bill = this.revenues.total.to_invoice + this.costs.total.to_bill;
        return {
            invoiced_billed,
            to_invoice_to_bill,
            total: invoiced_billed + to_invoice_to_bill,
        };
    }
}

ThProjectProfitability.props = {
    data: Object,
    labels: Object,
    formatMonetary: Function,
    onClick: Function,
};
ThProjectProfitability.template = 'th_project_itc.ProjectProfitability';
