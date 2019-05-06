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

                _applyDomainOnValues(domains);
                _handleOpenSteps(open_cfg_step_lines)

            });
		});

        function _handleOpenSteps(open_cfg_step_lines) {
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
        }

        function _applyDomainOnValues(domains) {
            _.each(domains, function (domain, attr_id) {
                var $selection = config_form.find('#' + attr_id);
                var $options = $selection.find('.config_attr_value');
                _.each($options, function (option) {
                    var condition = domain[0][1];
                    if (condition == 'in' || config_form == '=') {
                        if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                            $(option).attr('disabled', true);
                            if (option.selected) {
                                option.selected = false;
                            };
                        } else {
                            $(option).attr('disabled', false);
                        };
                    } else if (condition == 'not in' || config_form == '!=') {
                        if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                            $(option).attr('disabled', false);
                        } else {
                            $(option).attr('disabled', true);
                            if (option.selected) {
                                option.selected = false;
                            };
                        };
                    };
                });
            });
        }

        function _onChangeConfigStep(event, next_step) {
            var flag = _checkRequiredFields(event)
            var config_step_header = config_form.find('.nav.nav-tabs');
            var current_config_step = config_step_header.find('.nav-item.config_step.active').attr('data-step-id');
            if (flag) {
                return ajax.jsonRpc("/website_product_configurator/save_configuration", 'call', {
                    form_values: config_form.serializeArray(),
                    next_step: next_step || false,
                    current_step: current_config_step || false,
                }).then(function(data) {
                    if (data.error) {
                        alert(data.error);
                    };
                    return data;
                });
            } else {
                return false;
            }
        };
        
        function _displayTooltip(config_attribut) {
            $(config_attribut).focus();
            $(config_attribut).tooltip({
                title: "Please select an item in the list.",
                placement: "bottom",
                trigger: "manual",
                delay: {show: 500, hide: 500},
                template: "<div class='tooltip'><div class='tooltip-arrow'></div><div class='tooltip-inner'></div></div>"
            }).tooltip('show');
            setTimeout(function(){
                $(config_attribut).tooltip('hide');
            }, 2000);
        };

        function _checkRequiredFields(event) {
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.in');
            var config_attr = active_step.find('.form-control.config_attribute');
            var flag = true;
            for (var i = 0; i < config_attr.length; i++) {
               if ($(config_attr[i]).hasClass('required_config_attrib') && !config_attr[i].value) {
                    flag = false;
                    _displayTooltip(config_attr[i]);
                    break;
               };
            };
            return flag;
        };

        config_form.find('.config_step').click(function (event) {
            var next_step = event.currentTarget.getAttribute('data-step-id');
            var result = _onChangeConfigStep(event, next_step);
            if (!result) {
                event.preventDefault();
                event.stopPropagation();
            };
        });

        function _openNextStep(step) {
            var config_step_header = config_form.find('.nav.nav-tabs');
            var config_step = config_step_header.find('.nav-item.config_step.active');
            if (config_step.length) {
                config_step.removeClass('active');
            }
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.in');
            active_step.removeClass('active in');

            var next_step = config_step_header.find('.nav-item.config_step[data-step-id=' + step + ']');
            if (next_step.length) {
                next_step.addClass('active');
                var selector = next_step.find('a:first-child').attr('href');
                var step_to_active = config_form.find('.tab-content').find(selector);
                step_to_active.addClass('active in');
            }
        };

        function addRequiredAttr(config_step) {
            config_step = config_form.find('.tab-content').find('tab-pane container[data-step-id=' + config_step + ']');
            _.each(config_step.find('.form-control.config_attribute'), function(attribute_field) {
                $(attribute_field).attr('required', true);
            });
        };

        config_form.submit(function (event) {
            event.preventDefault();
            event.stopPropagation();

            var result = _onChangeConfigStep(event);
            if (result) {
                result.then(function (data) {
                    if (data) {
                        if (data.next_step) {
                            _openNextStep(data.next_step);
                        };
                        if (data.redirect_url) {
                            window.location = data.redirect_url;
                        };
                    };
                });
            }
        });
	 });

});
