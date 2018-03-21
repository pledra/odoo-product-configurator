/* Add one more option to boolean_button form widget (displayed in the product.template form view) */
odoo.define('product_configurator.FormView', function (require) {
"use strict";

var core = require('web.core');
var _t = core._t;

var FieldBooleanButton = core.form_widget_registry.map['boolean_button'].extend({
    init: function() {
        this._super.apply(this, arguments);
        switch (this.options["terminology"]) {
            case "config":
                this.string_true = _t("Configurable");
                this.hover_true = _t("Deactivate");
                this.string_false = _t("Standard");
                this.hover_false = _t("Activate");
                break;
        }
    },
});


core.form_widget_registry.add('boolean_button', FieldBooleanButton);

});
