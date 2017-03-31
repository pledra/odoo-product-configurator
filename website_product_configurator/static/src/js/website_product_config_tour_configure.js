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
        trigger: "#cfg_total:contains(28,750.00)",
    },
    {
        content: "Select fuel",
        trigger: "select.cfg_input:enabled:has(option:contains('Gasoline'))",
        run: function() {
            var option = $('select.cfg_input option:contains("Gasoline")');
            var select = option.parent();
            select.val(option.val()).change();
        }
    },
    {
        content: "Select engine",
        trigger: "select.cfg_input:enabled:has(option:contains('228i'))",
        run: function() {
            var option = $("select.cfg_input option:contains('228i')");
            var select = option.parent();
            option.parent().val(option.val())
            select.val(option.val()).change();
        },
    },
    {
        content: "Check engine price",
        trigger: "#cfg_price_tags:has(span:contains(12,634.00))"
    },
    {
        content: "Check total price",
        trigger: "#cfg_total:contains(43,279.10)"
    },
    {
        content: "Next Step",
        trigger: "#submit_configuration"
    },
    {
        content: "Select color",
        trigger: "select.cfg_input:enabled:has(option:contains('Silver'))",
        run: function() {
            var option = $('select.cfg_input option:contains("Silver")');
            var select = option.parent()
            select.val(option.val()).change();
        },
    },
    {
        content: "Select rims",
        trigger: "select.cfg_input:enabled:has(option:contains('Double-spoke 18'))",
        run: function() {
            var option = $('select.cfg_input option:contains("Double-spoke 18")');
            var select = option.parent()
            select.val(option.val()).change();
        },
    },
    {
        content: "Check rims price",
        trigger: "#cfg_price_tags:has(span:contains(726.00))"
    },
    {
        content: "Check total price",
        trigger: "#cfg_total:contains(44,114.00)",
    },
    {
        content: "Next Step",
        trigger: "#submit_configuration"
    },
    {
        content: "Select interior step",
        extra_trigger: "label:contains('Lines')",
        trigger: "#cfg_statusbar a:has(span:contains('Interior'))",
    },
    {
        content: "Select interior",
        trigger: "select.cfg_input:enabled:has(option:contains('Black'))",
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
        content: "Select Smoker Package Option",
        trigger: "#cfg_price_tags:has(div.label:contains('Transmission: Sport Automatic Transmission Steptronic'))",
        run: function() {
            var checkbox = $("strong:contains('Smoker Package')").parent().parent().siblings('label').find('input');
            checkbox.click();
        }
    },
    {
        content: "Select Tow Hook Option",
        trigger: "#cfg_price_tags:has(div.label:contains('Options: Smoker Package'))",
        run: function() {
            var checkbox = $("strong:contains('Tow hook')").parent().parent().siblings('label').find('input');
            checkbox.click();
        }
    },
    {
        content: "Check price",
        trigger: "#cfg_total:contains(45,298.50)",
    },
    {
        content: "Submit Configuration",
        trigger: "#submit_configuration"
    },
    {
        content: "Check configuration price",
        trigger: "b.oe_price span.oe_currency_value:contains(45,298.50)"
    },
    {
        content: 'Add to cart',
        trigger: '#add_to_cart'
    },
    {
        content: "Finished",
        trigger: "h1:contains('Shopping Cart')",
    }
]
);

});
