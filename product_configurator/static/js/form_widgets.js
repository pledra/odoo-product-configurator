/* Add one more option to boolean_button form widget (displayed in the product.template form view) */
odoo.define('product_configurator.FieldBooleanButton', function (require) {
"use strict";
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');

    var FormController = require('web.FormController');
    var ListController = require('web.ListController');
    var KanbanController = require('web.KanbanController');

    var pyUtils = require('web.py_utils');
    var core = require('web.core');
    var _lt = core._lt;

    var FieldBooleanButton = basic_fields.FieldBoolean.extend({
        description: _lt("Button"),
        className: basic_fields.FieldBoolean.prototype.className + ' o_boolean_button',
        events: {
            'click': '_onToggleButton',
            'hover': '_onHoverButton'
        },
        supportedFieldTypes: ['boolean'],
        _render: function() {
            this._super.apply(this, arguments);
            this.$el.removeClass('custom-control');
            this.$el.empty();
            this.text = this.value ? this.attrs.options.active : this.attrs.options.inactive;
            this.hover = this.value ? this.attrs.options.inactive : this.attrs.options.active;
            var val_color = this.value ? 'text-success' : 'text-danger';
            var hover_color = this.value ? 'text-danger' : 'text-success';
            var $val = $('<span>').addClass('o_stat_text o_not_hover ' + val_color).text(this.text);
            var $hover = $('<span>').addClass('o_stat_text o_hover d-none ' + hover_color).text(this.hover);
            this.$el.append($val).append($hover);
        },

        _onToggleButton: function (event) {
            event.stopPropagation();
            this._setValue(!this.value);
        },
    });

    FormController.include({
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
                this.$buttons.find('.o_form_button_create').css('display', 'none')
            }
        },

        _onButtonClicked: function (event) {
            var self = this;
            var attrs = event.data.attrs
            if (event.data.attrs.context) {
                var btn_ctx = pyUtils.eval('context', event.data.attrs);
                var record_ctx = self.model.get(event.data.record.id).context;
                self.model.localData[event.data.record.id].context = _.extend({}, btn_ctx, record_ctx)
            }
            if (attrs.special === 'no_save') {
                this.canBeSaved = function() {
                    return true;
                }
                var event_no_save = $.extend( true, {}, event );
                event_no_save.data.attrs.special = false;
                return this._super(event_no_save);
            }
            this._super(event);
        },
    });
    ListController.include({
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
                this.$buttons.find('.o_list_button_add').css('display', 'none')
            }
        },
    });
    KanbanController.include({
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if(self.modelName == 'product.product' && self.initialState.context.custom_create_variant) {
                this.$buttons.find('.o-kanban-button-new').css('display', 'none')
            }
        },
    });

    registry.add('boolean_button', FieldBooleanButton);
    return FieldBooleanButton
});
