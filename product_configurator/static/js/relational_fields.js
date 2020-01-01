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

    /* Bug from odoo: in case of widget many2many_tags $input and $el do not exist
    in 'this', so it returns 'undefine', but setIDForLabel(method in AbstractField)
    expecting getFocusableElement always return object*/
    fields.FieldMany2One.include({
        getFocusableElement: function () {
            var element = this._super.apply(this, arguments);
            if (element === undefined) {
                return $();
            }
            return element;
        },
    });
});
