/* Add one more option to boolean_button form widget (displayed in the product.template form view) */

odoo.define('product_configurator.FormView', function (require) {
  "use strict";

  var core = require('web.core');
  var ListView = require('web.ListView');
  var FormView = require('web.FormView');
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

  ListView.include({
    render_buttons: function() {
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.model == 'product.product' && self.dataset.context.custom_create_variant) {
        this.$buttons.find('.o_list_button_add').css('display', 'none')
        this.$buttons.find('.o_list_button_add_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_list_button_add_custom', function(ev) {
          ev.preventDefault();
          self.rpc("/web/action/load", {action_id: "product_configurator.action_wizard_product_configurator" }).done(function(result) {
            self.do_action(result);
          });
          return false;
        });
      }
    },
  });

  FormView.include({
    render_buttons: function($node){
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.model == 'product.product' && self.dataset.context.custom_create_variant) {
        this.$buttons.find('.o_form_button_create').css('display', 'none')
        this.$buttons.find('.o_form_button_create_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_form_button_create_custom', function(ev) {
          ev.preventDefault();
          self.rpc("/web/action/load", {action_id: "product_configurator.action_wizard_product_configurator" }).done(function(result) {
            self.do_action(result);
          });
          return false;
        });
      }
    },
});


core.form_widget_registry.add('boolean_button', FieldBooleanButton);

});
