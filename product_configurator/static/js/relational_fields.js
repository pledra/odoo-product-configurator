odoo.define('product_configurator.FieldStatus', function (require) {
    "use strict";

    var fields = require('web.relational_fields');
    var FieldStatus = fields.FieldStatus

    FieldStatus.include({

        /* Prase input as string in order to have a clickable statusbar*/
        _onClickStage: function (e) {
            if ( this.model.startsWith('product.configurator') ) {
                this._setValue(String($(e.currentTarget).data("value")));
            }
            else {
                this._super(e);
            }
        },

    });
});
