odoo.define('product_configurator_mrp.ListController', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var qweb = core.qweb;

    var ConfigListController = ListController.extend({
        buttons_template: 'ConfigListView.buttons',
        events: _.extend({}, ListController.prototype.events, {
            'click .o_list_button_add_config': '_onConfigure',
        }),

        renderButtons: function () {
            var self = this;
            self._super.apply(this, arguments);
            if (this.$buttons && self.modelName == 'mrp.production' && self.initialState.context.custom_create_variant) {
                this.$buttons.find('.o_list_button_add_config').css('display', 'inline');
            }
        },

        _onConfigure: function (ev) {
            var self = this;
            return this._rpc({
                model: 'mrp.production',
                method: 'action_config_start',
                args: [""],
                context: this.initialState.context,
            }).then(function(result) {
                self.do_action(result);
            });
        },
    });

    var ConfigListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: ConfigListController,
        }),
    });

    viewRegistry.add('product_configurator_mrp_tree', ConfigListView);

});
