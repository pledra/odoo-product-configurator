/* Add one more option to boolean_button form widget (displayed in the product.template form view) */
odoo.define('product_configurator.FormView', function (require) {
"use strict";

var core = require('web.core');
var field_registry = require('web.field_registry');
var _t = core._t;

var FieldBooleanButton = field_registry.map['boolean_button'].extend({
    init: function() {
        this._super.apply(this, arguments);
        var terminology = this.attrs.options && this.attrs.options['terminology'];
        switch (terminology) {
            case "config":
                this.string_true = _t("Configurable");
                this.hover_true = _t("Deactivate");
                this.string_false = _t("Standard");
                this.hover_false = _t("Activate");
                break;
        }
    },
});


field_registry.add('boolean_button', FieldBooleanButton);

});
