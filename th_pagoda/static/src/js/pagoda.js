/** @odoo-module **/


const { Component, useState, onWillStart, onWillUnmount } = owl;
import { registry } from "@web/core/registry";
import session from 'web.session';
import rpc from 'web.rpc';

class PagodaHomepage extends Component{
    setup() {
        super.setup();
        this.state = useState({
            count: 0
        });
        this.uid = session.user_id[0];
        onWillStart(async ()=>{
            return Promise.all([this.fetch_data()]);
        });
        this.saveInterval = setInterval(this.save_data.bind(this), 5000);


        onWillUnmount(() =>{
           clearInterval(this.saveInterval);
        });


    }
    increase () {
        this.state.count ++;
    }

    onChangeState(){
        if(this.state.count% 10 != 0) return
        this.save_data()
    }


    async fetch_data(){
        let result = await rpc.query({
            model: 'res.users',
            method: 'search_read',
            domain: [['id', '=', this.uid]],
            fields: ['pg_check_click']
        });
        this.state.count = result[0]['pg_check_click']

    }
    async save_data(){
        rpc.query({
               model: 'res.users',
               method: 'write',
               args: [this.uid, {pg_check_click: this.state.count}]
           });
    }


}
PagodaHomepage.template = "th_pagoda.PagodaHomepage";
registry.category("actions").add("th_pagoda", PagodaHomepage);