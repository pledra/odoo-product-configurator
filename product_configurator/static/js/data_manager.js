odoo.define('product_configurator.DataManager', function (require) {
    "use strict";

    var Manager = require('web.DataManager');

    Manager.include({

        /**
        * Disable view caching for product.configurator model as it has a very
        * heavy reliance on the fields_view_get method to generate and update
        * dynamic content.
        */
        load_views: function (params, options) {
            if (params.context['view_cache'] == false) {
                this.invalidate();
            }
            return this._super(params, options);
        }
    });
});
