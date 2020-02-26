odoo.define('product_configurator_mrp.FormController', function (require) {
"use strict";

var core = require('web.core');
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var viewRegistry = require('web.view_registry');

    var qweb = core.qweb;

    var ConfigFormController = FormController.extend({
        buttons_template: 'ConfigFormView.buttons',
        events: _.extend({}, FormController.prototype.events, {
            'click .o_form_button_create_config': '_onConfigure',
        }),

        renderButtons: function ($node) {
            var self = this;
            var $footer = this.footerToButtons ? this.renderer.$('footer') : null;
            var mustRenderFooterButtons = $footer && $footer.length;
            self._super.apply(this, arguments);
            if (mustRenderFooterButtons) {
            } else {
                if (this.$buttons && self.modelName == 'mrp.production' && self.initialState.context.custom_create_variant) {
                    var button_create = this.$buttons.find('.o_form_button_create');
                    button_create.after(qweb.render("ConfigFormView.buttons", {widget: this}));
                    this.$buttons.find('.o_form_button_create_config').css('display', 'inline');
                }
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

    var ConfigFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: ConfigFormController,
        }),
    });

    viewRegistry.add('product_configurator_mrp_form', ConfigFormView);

});
