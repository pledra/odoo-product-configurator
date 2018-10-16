/* Add one more option to boolean_button form widget (displayed in the product.template form view) */
odoo.define('product_configurator.FormView', function (require) {
"use strict";
  var core = require('web.core');
  var ListView = require('web.ListController');
  var FormView = require('web.FormController');
  var KanbanController = require('web.KanbanController');
  var AbstractField = require('web.AbstractField');
  var registry = require('web.field_registry');
  var basic_fields = require('web.basic_fields');
  var _t = core._t;

  var FieldBooleanButton = basic_fields.FieldBooleanButton.extend({
      _render: function() {
        this._super.apply(this, arguments);
        switch (this.nodeOptions.terminology) {
            case "config":
                this.$el.empty();
                this.text = this.value ? _t("Configurable") : _t("Standard");
                this.hover = this.value ? _t("Standard") : _t("Configurable");
                var val_color = this.value ? 'text-success' : 'text-danger';
                var hover_color = this.value ? 'text-danger' : 'text-success';
                var $val = $('<span>').addClass('o_stat_text o_not_hover ' + val_color).text(this.text);
                var $hover = $('<span>').addClass('o_stat_text o_hover ' + hover_color).text(this.hover);
                this.$el.append($val).append($hover);
                break;
        }
      },
    });

  KanbanController.include({
    renderButtons: function ($node) {
      var self = this;
      this._super.apply(this, arguments);
      if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
        this.$buttons.find('.o-kanban-button-new').css('display', 'none')
        this.$buttons.find('.o_kanban_button_create_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_kanban_button_create_custom', function(ev) {
          ev.preventDefault();
          return self.do_action({
            name: 'Product Configurator',
            res_model: 'product.configurator',
            views: [[false, 'form']],
            type: 'ir.actions.act_window',
            view_type: 'form',
            view_mode: 'form',
            target: 'new'
          });
          return false;
        });
      }
    },
  })


  ListView.include({
    renderButtons: function() {
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
        this.$buttons.find('.o_list_button_add').css('display', 'none')
        this.$buttons.find('.o_list_button_add_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_list_button_add_custom', function(ev) {
          ev.preventDefault();
          return self.do_action({
            name: 'Product Configurator',
            res_model: 'product.configurator',
            views: [[false, 'form']],
            type: 'ir.actions.act_window',
            view_type: 'form',
            view_mode: 'form',
            target: 'new'
          });
          return false;
        });
      }
    },
  });
  FormView.include({
    renderButtons: function ($node) {
      var self = this;
      this._super.apply(this, arguments); // Sets this.$buttons
      if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
        this.$buttons.find('.o_form_button_create').css('display', 'none')
        this.$buttons.find('.oe_form_button_create').css('display', 'none')
        this.$buttons.find('.o_form_button_create_custom').css('display', 'inline')
        this.$buttons.on('click', '.o_form_button_create_custom', function(ev) {
        ev.preventDefault();
          return self.do_action({
            name: 'Product Configurator',
            res_model: 'product.configurator',
            views: [[false, 'form']],
            type: 'ir.actions.act_window',
            view_type: 'form',
            view_mode: 'form',
            target: 'new'
          });
        });
      }
    },
    _onButtonClicked: function (event) {
        var attrs = event.data.attrs
        if (attrs.special === 'no_save') {
          this.canBeSaved = function() {return true;}
          var event_no_save = $.extend( true, {}, event );
          event_no_save.data.attrs.special = false;
          return this._super(event_no_save);
        }
        this._super(event);
    },
  });
  registry.add('boolean_button', FieldBooleanButton);
});
