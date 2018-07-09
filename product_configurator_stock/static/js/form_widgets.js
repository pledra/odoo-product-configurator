/* Add one more option to boolean_button form widget (displayed in the product.template form view) */

odoo.define('product_configurator_lot.FormView', function (require) {
  "use strict";

  var core = require('web.core');
  var ListController = require('web.ListController');
  var FormController = require('web.FormController');
  var _t = core._t;

  ListController.include({
    renderButtons: function ($node) {
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.modelName == 'stock.production.lot' && self.initialState.context.custom_create_variant) {
        this.$buttons.find('.o_list_button_add').css('display', 'none')
        this.$buttons.find('.o_list_button_add_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_list_button_add_custom', function(ev) {
          ev.preventDefault();
          return self._rpc({
            route: '/web/action/load',
            params: {action_id: "product_configurator_stock.action_wizard_product_configurator_lot"}
          }).then(function (action) {
            self.do_action(action);
          });
        });
      }
    },
  });

  FormController.include({
    renderButtons: function ($node){
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.modelName == 'stock.production.lot' && self.initialState.context.custom_create_variant) {
        this.$buttons.find('.o_form_button_create').css('display', 'none')
        this.$buttons.find('.oe_form_button_create').css('display', 'none')
        this.$buttons.find('.o_form_button_create_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_form_button_create_custom', function(ev) {
          ev.preventDefault();
          return self._rpc({
            route: '/web/action/load',
            params: {action_id: "product_configurator_stock.action_wizard_product_configurator_lot" }
          }).then(function (action) {
            self.do_action(action);
          });
        });
      }
    },
});
});
