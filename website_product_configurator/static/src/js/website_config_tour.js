odoo.define("website_product_configurator.tour_configuration", function (require) {
    "use strict";

    var core = require("web.core");
    var tour = require("web_tour.tour");
    var base = require("web_editor.base");

    var _t = core._t;

    tour.register("config", {
        url: "/shop/product/2-series-39",
        wait_for: base.ready(),
    }, [{
        trigger: "form#product_config_form",
        content: _t("Let's configure your first product."),
    }]);
});
