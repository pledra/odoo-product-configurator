odoo.define("website_product_configurator.tour_configuration", function (require) {
    "use strict";

    var core = require("web.core");
    var tour = require("web_tour.tour");
    var base = require("web_editor.base");

    var _t = core._t;

    tour.register("config", {
        url: "/shop",
        wait_for: base.ready(),
    },
        [
            {
                content: "search 2 series",
                trigger: 'form input[name="search"]',
                run: "text 2 series",
            },
            {
                content: "search 2 series",
                trigger: 'form:has(input[name="search"]) .oe_search_button',
            },
            {
                content: "select 2 series",
                trigger: '.oe_product_cart a:contains("2 Series")',
            },
            {
                content: "click to select fuel",
                trigger: 'div.tab-pane.container.fade.active.in select:first',
                extra_trigger: '.nav-item.config_step.active a:contains(Engine)',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select:first option:contains(Gasoline)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select:first option:contains(Gasoline)').closest('select').change()
                }
            },
            {
                content: "click to select engine",
                trigger: '.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(218i)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(218i)').closest('select').change()
                }
            },
            {
                content: "click on continue",
                trigger: '#form_action span:contains(Continue)',
            },
            {
                content: "click to select color",
                extra_trigger: '.nav-item.config_step.active a:contains(Body)',
                trigger: 'div.tab-pane.container.fade.active.in select:first',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select:first option:contains(Silver)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select:first option:contains(Silver)').closest('select').change()
                }
            },
            {
                content: "click to select rims",
                trigger: 'div.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(V-spoke 16)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(V-spoke 16)').closest('select').change()
                }
            },
            {
                content: "click on continue",
                trigger: '#form_action span:contains(Continue)',
            },
            {
                content: "click to select Lines",
                extra_trigger: '.nav-item.config_step.active a:contains(Lines)',
                trigger: '.tab-pane.container.fade.active.in select:first',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select:first option:contains(Sport Line)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select:first option:contains(Sport Line)').closest('select').change()
                }
            },
            {
                content: "click on continue",
                trigger: '#form_action span:contains(Continue)',
            },
            {
                content: "click to select tapistry",
                extra_trigger: '.nav-item.config_step.active a:contains(Interior)',
                trigger: 'div.tab-pane.container.fade.active.in select:first',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select:first option:contains(Black)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select:first option:contains(Black)').closest('select').change()
                }
            },
            {
                content: "click on continue",
                trigger: '#form_action span:contains(Continue)',
            },
            {
                content: "click to select Transmission",
                extra_trigger: '.nav-item.config_step.active a:contains(Extras)',
                trigger: 'div.tab-pane.container.fade.active.in select:first',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select:first option:contains("Automatic (Steptronic)")')[0].selected = true
                    $('.tab-pane.container.fade.active.in select:first option:contains("Automatic (Steptronic)")').closest('select').change()
                }
            },
            {
                content: "click to select Options",
                trigger: 'div.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib',
                run: function (argument) {
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(Armrest)')[0].selected = true
                    $('.tab-pane.container.fade.active.in select.form-control.config_attribute.required_config_attrib option:contains(Armrest)').closest('select').change()
                }
            },
            {
                content: "click on continue",
                trigger: '#form_action span:contains(Continue)',
            },
        ]);
});
