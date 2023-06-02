/** @odoo-module **/


const {Component, useState, onWillStart, onWillUnmount, onWillUpdateProps, onWillPatch} = owl;
import {registry} from "@web/core/registry";
import session from 'web.session';
import rpc from 'web.rpc';

class PagodaHomepage extends Component {
    setup() {
        super.setup();
        this.state = useState({
            count: 0,
            all_user:[]
        });
        this.current_class = '';
        this.uid = session.user_id[0];
        onWillStart(async () => {
            window.addEventListener('beforeunload', this._onBeforeUnload);
            return Promise.all([this.fetch_data(), this.search_user()]);

        });
        // this.saveInterval = setInterval(this.save_data.bind(this), 5000);
        this.refreshUserInterval = setInterval(this.search_user.bind(this), 10000);

        onWillUpdateProps(async (nextProps) => {
            debugger
            // this.fieldInfo = await this.loadField(nextProps.resModel, nextProps.node.operands[0]);
        });
        onWillPatch(() => {
            debugger
            this.scrollState = this.getScrollSTate();
        });


        onWillUnmount(() => {
            clearInterval(this.saveInterval);
            clearInterval(this.refreshUserInterval);
        });

    }

    stopPropagation(){
        debugger
    }

    getScrollSTate(){
        return 1
    }

    increase() {
        this.state.count++;
        this.current_class = this.current_class ? '' : 'click_stick';
    }

    onChangeState() {
        debugger
        if (this.state.count % 10 != 0) return
        this.save_data()
    }

    async fetch_data() {
        let result = await rpc.query({
            model: 'res.users',
            method: 'search_read',
            domain: [['id', '=', this.uid]],
            fields: ['pg_check_click']
        });
        this.state.count = result[0]['pg_check_click']

    }

    async save_data() {
        rpc.query({
            model: 'res.users',
            method: 'write',
            args: [this.uid, {pg_check_click: this.state.count}]
        });

    }

    async search_user() {
        let result = await rpc.query({
            model: 'res.users',
            method: 'search_read',
            args: [[]],
            fields: ['name', 'pg_check_click'],
            limit: 10,
        });
        result.sort((a,b) => b.pg_check_click - a.pg_check_click);

        this.state.all_user = result
    }


}

PagodaHomepage.template = "th_pagoda.PagodaHomepage";
registry.category("actions").add("th_pagoda", PagodaHomepage);