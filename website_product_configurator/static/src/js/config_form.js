odoo.define('website_product_configurator.config_form', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var time = require('web.time');

    $(document).ready(function () {
        var config_form = $("#product_config_form");
        var datetimepickers_options = {
            calendarWeeks: true,
            icons : {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                next: 'fa fa-chevron-right',
                previous: 'fa fa-chevron-left',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down',
               },
            locale : moment.locale(),
            widgetParent: 'body',
            allowInputToggle: true,
            showClose: true,
            format : time.getLangDatetimeFormat(),
            keyBinds: null,
        };

        var datepickers_options = $.extend({}, datetimepickers_options, {format: time.getLangDateFormat()})

        config_form.find('.product_config_datetimepicker').datetimepicker(datetimepickers_options);
        config_form.find('.product_config_datepicker').datetimepicker(datepickers_options);

        /* Monitor input changes in the configuration form and call the backend onchange method*/
        config_form.find('.config_attribute').change(function(ev) {
            ajax.jsonRpc("/website_product_configurator/onchange", 'call', {
                form_values: config_form.serializeArray(),
                field_name: $(this)[0].name,
            }).then(function(data) {
                if (data.error) {
                    alert(data.error);
                };
                var values = data.value;
                var domains = data.domain;

                var open_cfg_step_line_ids = data.open_cfg_step_line_ids;
                var config_image_vals = data.config_image_vals;

                _applyDomainOnValues(domains);
                _handleOpenSteps(open_cfg_step_line_ids);
                _setImageUrl(config_image_vals);
                _setWeightPrice(values.weight, values.price);
            });
            _handleCustomAttribute(ev)
        });

        function _setWeightPrice(weight, price) {
            var formatted_price = _.str.sprintf('%.2f', price);
            var formatted_weight = _.str.sprintf('%.1f', weight);
            $('.config_product_weight').text(formatted_weight);
            $('.config_product_price').find('.oe_currency_value').text(formatted_price);
        }

        function _setImageUrl(config_image_vals) {
            var images = '';
            if (config_image_vals){
                var model = config_image_vals.name
                config_image_vals.config_image_ids.forEach(function(line){
                    images += "<img id='cfg_image' itemprop='image' class='img img-responsive pull-right'"
                    images += "src='/web/image/"+model+"/"+line+"/image'/>"
                })
            }
            $('#product_config_image').html(images);
        };

        function _handleCustomAttribute(event) {
            var container = $(event.currentTarget).closest('.tab-pane.container');
            var attribute_id = $(event.currentTarget).attr('data-oe-id');
            var custom_value = container.find('.custom_config_value[data-oe-id=' + attribute_id + ']');
            var custom_value_container = custom_value.closest('.custom_field_container[data-oe-id=' + attribute_id + ']');
            if ($(event.currentTarget.selectedOptions[0]).hasClass('custom_config_attr_value') && custom_value_container.hasClass('hidden')) {
                custom_value_container.removeClass('hidden');
                custom_value.addClass('required_config_attrib');
            } else if (!custom_value_container.hasClass('hidden')){
                custom_value_container.addClass('hidden');
                if (custom_value.hasClass('required_config_attrib')) {
                    custom_value.removeClass('required_config_attrib');
                }
            }
        }

        function _handleOpenSteps(open_cfg_step_line_ids) {
            var $steps = config_form.find('.config_step');
            _.each($steps, function (step) {
                step = $(step);
                var step_id = step.attr('data-step-id');
                if ($.inArray(step_id, open_cfg_step_line_ids) < 0) {
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

        function _displayTooltip(config_attribut, message) {
            $(config_attribut).tooltip({
                title: message,
                placement: "bottom",
                trigger: "manual",
                delay: {show: 500, hide: 500},
                template: "<div class='tooltip'><div class='tooltip-arrow'></div><div class='tooltip-inner'></div></div>"
            }).tooltip('show');
            setTimeout(function(){
                $(config_attribut).tooltip('destroy');
            }, 4000);
        };

        function _checkRequiredFields(event) {
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.in');
            var config_attr = active_step.find('.form-control.required_config_attrib');
            var flag = true;
            for (var i = 0; i < config_attr.length; i++) {
                var cfg_attr_value = config_attr[i].value.trim()
                if (!cfg_attr_value  || cfg_attr_value == '0') {
                    $(config_attr[i]).addClass('textbox-border-color');
                    flag = false;
                    // if (config_attr[i].tagName == 'SELECT') {
                    //     var message = "Please select an item in the list."
                    // } else if (config_attr[i].tagName == 'INPUT') {
                    //     var message = "Please enter value."
                    // }
                    // _displayTooltip(config_attr[i], message);
                }
                else if (cfg_attr_value && $(config_attr[i]).hasClass('textbox-border-color')) {
                    $(config_attr[i]).removeClass('textbox-border-color');
                };
            };
            return flag;
        };

        config_form.find('.config_attribute').change(function (event) {
            var attribute = event.currentTarget;
            if (attribute.value.trim() && attribute.value.trim() != '0' && $(attribute).hasClass('textbox-border-color')) {
                $(attribute).removeClass('textbox-border-color');
            };
        });
        config_form.find('.custom_config_value').change(function (event) {
            var attribute = event.currentTarget;
            if (attribute.value.trim() && attribute.value.trim() != '0' && $(attribute).hasClass('textbox-border-color')) {
                $(attribute).removeClass('textbox-border-color');
            };
        });

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

        // Save Values
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

        // quantty sppiner
        function _disableEnableAddRemoveQtyButton(quantity, max_val, min_val) {
            if (quantity >= max_val) {
                $('.js_add_qty').addClass('btn-disabled');
            } else if (quantity < max_val && $('.js_add_qty').hasClass('btn-disabled')) {
                $('.js_add_qty').removeClass('btn-disabled');
            }
            if (quantity <= min_val) {
                $('.js_remove_qty').addClass('btn-disabled');
            } else if (quantity > min_val && $('.js_remove_qty').hasClass('btn-disabled')) {
                $('.js_remove_qty').removeClass('btn-disabled');
            }
        }

        function _handleSppinerCustomValue(ev) {
            ev.preventDefault();
            ev.stopPropagation();

            var current_target = $(ev.currentTarget);
            var custom_value = current_target.parent().find('input.custom_config_value');
            var quantity = parseFloat(custom_value.val() || 0);
            var max_val = parseFloat(custom_value.attr('max') || Infinity);
            var min_val = parseFloat(custom_value.attr('min') || 0);

            var new_qty = quantity;
            if (current_target.has(".fa-minus").length) {
                new_qty = quantity - 1;
            } else if (current_target.has(".fa-plus").length) {
                new_qty = quantity + 1;
            }
            if (new_qty > max_val) {
                var attribute_name = custom_value.closest('.tab-pane').find('label[data-oe-id="' + custom_value.attr('data-oe-id') + '"]');
                var message = "Selected custom value " + attribute_name.text() + " must be lower than " + (max_val + 1);
                _displayTooltip(custom_value, message);
                new_qty = max_val;
            }
            else if (new_qty < min_val) {
                var attribute_name = custom_value.closest('.tab-pane').find('label[data-oe-id="' + custom_value.attr('data-oe-id') + '"]');
                var message = "Selected custom value " + attribute_name.text() + " must be at least " + min_val;
                _displayTooltip(custom_value, message);
                new_qty = min_val;
            }
            custom_value.val(new_qty);
            _disableEnableAddRemoveQtyButton(new_qty ,max_val ,min_val)
        }

        $('.custom_config_value.quantity').change(function(ev) {
            _handleSppinerCustomValue(ev);
        });

        $('.js_add_qty').on('click', function(ev) {
            _handleSppinerCustomValue(ev);
        });

        $('.js_remove_qty').on('click', function(ev) {
            _handleSppinerCustomValue(ev);
        });
    });

})
