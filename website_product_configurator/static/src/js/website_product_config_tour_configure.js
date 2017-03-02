odoo.define('website_product_configurator.tour', function (require) {
'use strict';

var Tour = require('web.Tour');

Tour.register({
    id:   'configure_product',
    name: "Try to configure products",
    path: '/configurator',
    mode: 'test',
    steps: [
        {
            title:  "Select car",
            element: 'section a[href^="/configurator/2-series-"]',
        },
        {
            title: "Check price",
            element: "#cfg_total:contains(28,750.00)",
        },
        {
            title:  "Select fuel",
            element: "label span:contains('Fuel')",
            onload: function() {
                var option = $('select.cfg_input option:contains("Gasoline")');
                var select = option.parent();
                select.val(option.val()).change();
            }
        },
        {
            title:  "Select engine",
            element: "label span:contains('Engine')",
            waitFor: "select.cfg_input:enabled option:not(.hidden):contains('228i')",
            onload: function() {
                var option = $("select.cfg_input option:contains('228i')");
                var select = option.parent();
                option.parent().val(option.val())
                select.val(option.val()).change();
            },
        },
        {
            title: "Check price",
            waitFor: "#cfg_total:contains(43,279.10)",
            element: "#cfg_price_tags:contains(div span:contains(12,634.00)"
        },
        {
            title: "Next Step",
            element: "#submit_configuration"
        },
        {
            title:  "Select color",
            element: "label span:contains('Color')",
            waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Silver')",
            onload: function() {
                var option = $('select.cfg_input option:contains("Silver")');
                var select = option.parent()
                select.val(option.val()).change();
            },
        },
        {
            title:  "Select rims",
            element: "label span:contains('Rims')",
            waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Double-spoke 18')",
            onload: function() {
                var option = $('select.cfg_input option:contains("Double-spoke 18")');
                var select = option.parent()
                select.val(option.val()).change();
            },
        },
        {
            title: "Check price",
            waitFor: "#cfg_total:contains(44,114.00)",
            element: "#cfg_price_tags:contains(div span:contains(726.00)"
        },
        {
            title: "Next Step",
            element: "#submit_configuration"
        },
        {
            title:     "Select interior step",
            waitFor:   "select.cfg_input",
            element:   "#cfg_statusbar a:contains('Interior')",
        },
        {
            title: "Select interior",
            element: "label span:contains('Tapistry')",
            waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Black')",
            onload: function() {
                var option = $('select.cfg_input option:contains("Black")');
                var select = option.parent();
                select.val(option.val()).change();
            },
        },
        {
            title: "Next Step",
            element: "#submit_configuration"
        },
        {
            title: "Select transmission",
            element: "strong:contains('Automatic Sport (Steptronic)')",
            onload: function() {
                var radio = $("strong:contains('Automatic Sport (Steptronic)')").parent().parent().siblings('label').find('input')
                radio.click();
            }
        },
        {
            title: "Select options",
            element: "label:contains('Options')",
            onload: function() {
                var checkbox = $("strong:contains('Smoker Package')").parent().parent().siblings('label').find('input');
                checkbox.click();

                var checkbox = $("strong:contains('Tow hook')").parent().parent().siblings('label').find('input');
                checkbox.click();
            }
        },
        {
            title: "Check price",
            element: "#cfg_total:contains(45,298.50)",
        },
        {
            title: "Submit Configuration",
            element: "#submit_configuration"
        },
        {
            title: "Check configuration price",
            element: "b.oe_price span.oe_currency_value:contains(45,298.50)"
        },
        {
            title: 'Add to cart',
            element: '#add_to_cart'
        },
        {
            title:     "Finished",
            waitFor:   "h1:contains('Shopping Cart')",
        }
    ]
});

});
