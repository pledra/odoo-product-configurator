odoo.define('product_configurator.FieldStatus', function (require) {
    "use strict";

    var fields = require('web.relational_fields');
    var FieldStatus = fields.FieldStatus

    FieldStatus.include({

        /* Prase input as string in order to have a clickable statusbar*/
        _onClickStage: function (e) {
            this._setValue(String($(e.currentTarget).data("value")));
        },

    });
});
