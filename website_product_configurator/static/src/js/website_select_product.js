odoo.define("website_product_configurator.select_product_radio", function (require) {
    "use strict";

    var core = require("web.core");
    var base = require("web_editor.base");
    var tour = require("web_tour.tour");

    $('.image_config_attr_value_radio').on("click", function(event) {
        var val_id = $(this).data('val-id')
        _.each($('.config_attr_value'), function (value, key) {
            if (val_id == $(value).val()){
                $(value).prop('checked', 'checked')
            }
        })
    });
    
});
