odoo.define('pos_mt.exactmoney', function (require) {
"use strict";

var gui     = require('point_of_sale.gui');

gui.Gui = gui.Gui.extend({
        numpad_input: function(buffer, input, options){
            var newbuf  = buffer.slice(0);
            var amount_due = this.pos.get_order().get_due();
            if (input=='PAS'){
                newbuf = this.chrome.format_currency_no_symbol(amount_due);
            } else {
                return this._super(buffer, input, options);   
            }

            return newbuf;
            

        }

});

});
