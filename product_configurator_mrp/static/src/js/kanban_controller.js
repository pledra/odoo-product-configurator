odoo.define('product_configurator_mrp.KanbanController', function (require) {
"use strict";

    var core = require('web.core');
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');

    var qweb = core.qweb;

    var ConfigKanbanController = KanbanController.extend({
        buttons_template: 'ConfigKanbanView.buttons',
        events: _.extend({}, KanbanController.prototype.events, {
            'click .o-kanban-button-new_config': '_onConfigure',
        }),

        renderButtons: function () {
            var self = this;
            self._super.apply(this, arguments);
            if (this.$buttons && self.modelName == 'mrp.production' && self.initialState.context.custom_create_variant) {
                this.$buttons.find('.o-kanban-button-new_config').css('display', 'inline');
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

    var ConfigKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: ConfigKanbanController,
        }),
    });

    viewRegistry.add('product_configurator_mrp_kanban', ConfigKanbanView);

});
