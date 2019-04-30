odoo.define('website_product_configurator.config_form', function (require) {
    'use strict';

    var ajax = require('web.ajax');

	$(document).ready(function () {
	    var config_form = $("#product_config_form");

	 	/* Monitor input changes in the configuration form and call the backend onchange method*/
	 	config_form.find('.config_attribute').change(function(ev) {
			ajax.jsonRpc("/website_product_configurator/onchange", 'call', {
                form_values: config_form.serializeArray(),
                field_name: $(this)[0].name,
            }).then(function(data) {
                var values = data.value;
                var domains = data.domain;
                var open_cfg_step_lines = data.open_cfg_step_lines;

                // Domain
                _.each(domains, function (domain, attr_id) {
                    var $selection = config_form.find('#' + attr_id);
                    var $options = $selection.find('.config_attr_value');
                    _.each($options, function (option) {
                        var condition = domain[0][1];
                        if (condition == 'in' || config_form == '=') {
                            if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                                $(option).attr('disabled', true);
                            } else {
                                $(option).attr('disabled', false);
                            };
                        } else if (condition == 'not in' || config_form == '!=') {
                            if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                                $(option).attr('disabled', false);
                            } else {
                                $(option).attr('disabled', true);
                            };
                        };
                    });
                });

                // Open steps
                var $steps = config_form.find('.config_step');
                _.each($steps, function (step) {
                    step = $(step);
                    var step_id = step.attr('data-step-id');
                    if ($.inArray(parseInt(step_id), open_cfg_step_lines) < 0) {
                        if (!step.hasClass('hidden')) {
                            step.addClass('hidden');
                        };
                    } else {
                        if (step.hasClass('hidden')) {
                            step.removeClass('hidden');
                        };
                    };
                });
            	debugger;
            });
		});

        function _onChangeConfigStep(event) {
            return ajax.jsonRpc("/website_product_configurator/save_configuration", 'call', {
                form_values: config_form.serializeArray(),
            }).then(function(data) {
                if (!data) {
                    alert("ERROR");
                }
                return data;
            });
        };

        function configure_product() {
            console.log("################### configure_product");
        };

        function active_step_body(next_step) {
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.in');
            active_step.removeClass('active in');

            var selector = next_step.find('a:first-child').attr('href');
            var step_to_active = config_form.find('.tab-content').find(selector);
            step_to_active.addClass('active in');
        };

        config_form.find('.config_step').click(_onChangeConfigStep);
        config_form.submit(function (event) {
            event.preventDefault();
            event.stopPropagation();

            var result = _onChangeConfigStep(event);
            result.then(function (data) {
                var next_step;
                if (data) {
                    var config_step = config_form.find('.nav.nav-tabs').find('.nav-item.config_step.active');
                    if (config_step.length) {
                        config_step.removeClass('active');
                        next_step = config_step.next();
                    } else {
                        config_step = config_form.find('.nav.nav-tabs').find('.nav-item.config_step');
                        next_step = $(config_step[0])
                    };
                    if (!next_step.length) {
                        configure_product();
                    } else {
                        next_step.addClass('active');
                        active_step_body(next_step)
                    }
                };
            });
        });
	 });

});