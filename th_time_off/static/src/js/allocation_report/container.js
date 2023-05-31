/** @odoo-module **/
const {Component, useState, onWillStart, useRef} = owl;
import {registry} from '@web/core/registry'
import rpc from 'web.rpc';

var session = require('web.session');
import {Content} from "./content";

export class Container extends Component {

    setup() {
        super.setup();
        this.state = useState({
            full_year: new Date().getFullYear(),
            action_name: this.props.action.name,
        })
        onWillStart(() => {
            return Promise.all([this._fetch_current_year()])
        })
        this.state.data = {
            lang: session.bundle_params.lang,
        }
    }

    async _fetch_current_year() {
        let current_year = new Date().getFullYear();
        let result = await rpc.query({
            model: 'allocation.report',
            method: 'get_lines',
            args: [[], current_year],
        });
        this.state.data_fetch = result;
        this.state.full_year = current_year;
    }

    async _fetch_previous_year() {
        let previous_year = new Date().getFullYear() - 1;
        let result = await rpc.query({
            model: 'allocation.report',
            method: 'get_lines',
            args: [[], previous_year],
        });
        this.state.data_fetch = result;
        this.state.full_year = previous_year;
    }

    async th_export_allo_to_xlsx() {
        let result = await rpc.query({
            model: 'allocation.report',
            method: 'get_report_customs',
            args: [[], this.state.data_fetch],
        });
    }

}

Container.template = 'th_time_off.container'
Container.components = {Content}

registry.category('actions').add('allocationReport', Container)


