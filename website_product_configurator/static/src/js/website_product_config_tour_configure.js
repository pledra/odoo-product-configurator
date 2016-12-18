odoo.define('website_product_configurator.tour', function (require) {
'use strict';

var tour = require('web_tour.tour');
var base = require("web_editor.base");

tour.register('configure_product', {
    test: true,
    url: '/configurator',
    wait_for: base.ready()
},
[
    {
        content: "Select car",
        trigger: 'section a[href^="/configurator/2-series-"]',
    },
    {
        content: "Check price",
        trigger: "#cfg_total:contains(25000)",
    },
    {
        content: "Select fuel",
        trigger: "label span:contains('Fuel')",
        run: function() {
            var option = $('select.cfg_input option:contains("Gasoline")');
            var select = option.parent();
            select.val(option.val()).change();
        }
    },
    {
        content: "Select engine",
        trigger: "label span:contains('Engine')",
        waitFor: "select.cfg_input:enabled option:not(.hidden):contains('228i')",
        run: function() {
            var option = $("select.cfg_input option:contains('228i')");
            var select = option.parent();
            option.parent().val(option.val())
            select.val(option.val()).change();
        },
    },
    {
        content: "Check price",
        waitFor: "#cfg_total:contains(37634)",
        trigger: "#cfg_price_tags:contains(div span:contains(12634)"
    },
    {
        content: "Next Step",
        trigger: "#submit_configuration"
    },
    {
        content: "Select color",
        trigger: "label span:contains('Color')",
        waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Silver')",
        run: function() {
            var option = $('select.cfg_input option:contains("Silver")');
            var select = option.parent()
            select.val(option.val()).change();
        },
    },
    {
        content: "Select rims",
        trigger: "label span:contains('Rims')",
        waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Double-spoke 18')",
        run: function() {
            var option = $('select.cfg_input option:contains("Double-spoke 18")');
            var select = option.parent()
            select.val(option.val()).change();
        },
    },
    {
        content: "Check price",
        waitFor: "#cfg_total:contains(38360)",
        trigger: "#cfg_price_tags:contains(div span:contains(726)"
    },
    {
        content: "Next Step",
        trigger: "#submit_configuration"
    },
    {
        content: "Select interior step",
        waitFor: "select.cfg_input",
        trigger: "#cfg_statusbar a:contains('Interior')",
    },
    {
        content: "Select interior",
        trigger: "label span:contains('Tapistry')",
        waitFor: "select.cfg_input:enabled option:not(.hidden):contains('Black')",
        run: function() {
            var option = $('select.cfg_input option:contains("Black")');
            var select = option.parent();
            select.val(option.val()).change();
        },
    },
    {
        content: "Next Step",
        trigger: "#submit_configuration"
    },
    {
        content: "Select transmission",
        trigger: "strong:contains('Automatic Sport (Steptronic)')",
        run: function() {
            var radio = $("strong:contains('Automatic Sport (Steptronic)')").parent().parent().siblings('label').find('input')
            radio.click();
        }
    },
    {
        content: "Select options",
        trigger: "label:contains('Options')",
        run: function() {
            var checkbox = $("strong:contains('Smoker Package')").parent().parent().siblings('label').find('input');
            checkbox.click();

            var checkbox = $("strong:contains('Tow hook')").parent().parent().siblings('label').find('input');
            checkbox.click();
        }
    },
    {
        content: "Check price",
        trigger: "#cfg_total:contains(39390)",
    },
    {
        content: "Submit Configuration",
        trigger: "#submit_configuration"
    },
    {
        content: "Check configuration price",
        trigger: "b.oe_price span.oe_currency_value:contains(39,390)"
    },
    {
        content: 'Add to cart',
        trigger: '#add_to_cart'
    },
    {
        content: "Finished",
        waitFor: "h1:contains('Shopping Cart')",
    }
]
);

});
