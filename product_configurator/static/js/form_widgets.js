/* Add one more option to boolean_button form widget (displayed in the product.template form view) */
odoo.define('product_configurator.FieldBooleanButton', function (require) {
"use strict";
    var core = require('web.core');
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');
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
    registry.add('boolean_button', FieldBooleanButton);
    return FieldBooleanButton
});



// var FieldToggleBoolean = AbstractField.extend({
//         description: _lt("Button"),
//         template: "toggle_button",
//         events: {
//                 'click': '_onToggleButton'
//         },
//         supportedFieldTypes: ['boolean'],

//         //--------------------------------------------------------------------------
//         // Public
//         //--------------------------------------------------------------------------

//         /**
//          * A boolean field is always set since false is a valid value.
//          *
//          * @override
//          */
//         isSet: function () {
//                 return true;
//         },

//         //--------------------------------------------------------------------------
//         // Private
//         //--------------------------------------------------------------------------

//         /**
//          * @override
//          * @private
//          */
//         _render: function () {
//                 this.$('i')
//                         .toggleClass('o_toggle_button_success', !!this.value)
//                         .toggleClass('text-muted', !this.value);
//                 var title = this.value ? this.attrs.options.active : this.attrs.options.inactive;
//                 this.$el.attr('title', title);
//                 this.$el.attr('aria-pressed', this.value);
//         },

//         //--------------------------------------------------------------------------
//         // Handlers
//         //--------------------------------------------------------------------------

//         /**
//          * Toggle the button
//          *
//          * @private
//          * @param {MouseEvent} event
//          */
//         _onToggleButton: function (event) {
//                 event.stopPropagation();
//                 this._setValue(!this.value);
//         },
// });
// });
