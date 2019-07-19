odoo.define('website_product_configurator.config_form', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var time = require('web.time');
    var utils = require('web.utils');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;

    var image_dict = {}

    $(document).ready(function () {
        if (!$.fn.datetimepicker) {
            ajax.loadJS("/web/static/lib/tempusdominus/tempusdominus.js");
        }
        var config_form = $("#product_config_form");
        var datetimepickers_options = {
            calendarWeeks: true,
            icons: {
                time: 'fa fa-clock-o',
                date: 'fa fa-calendar',
                up: 'fa fa-chevron-up',
                down: 'fa fa-chevron-down',
                previous: 'fa fa-chevron-left',
                next: 'fa fa-chevron-right',
                today: 'fa fa-calendar-check-o',
                clear: 'fa fa-delete',
                close: 'fa fa-times'
            },
            locale: moment.locale(),
            allowInputToggle: true,
            buttons: {
                showToday: true,
                showClose: true,
            },
            format: time.getLangDatetimeFormat(),
            keyBinds: null,
        };

        var datepickers_options = $.extend({}, datetimepickers_options, {format: time.getLangDateFormat()})

        config_form.find('.product_config_datetimepicker').parent().datetimepicker(datetimepickers_options);
        config_form.find('.product_config_datepicker').parent().datetimepicker(datepickers_options);
        config_form.find('.product_config_datepicker').parent().on('change.datetimepicker', function (event) {
            var attribute = $(event.currentTarget).find('input.required_config_attrib');
            _checkRequiredFields(attribute);
        });
        config_form.find('.product_config_datetimepicker').parent().on('change.datetimepicker', function (event) {
            var attribute = $(event.currentTarget).find('input.required_config_attrib');
            _checkRequiredFields(attribute);
        });

        /* Monitor input changes in the configuration form and call the backend onchange method*/
        config_form.find('.config_attribute').change(function(ev) {
            var form_data = config_form.serializeArray();
            for (var field_name in image_dict) {
                form_data.push({'name': field_name, 'value': image_dict[field_name]});
            }
            ajax.jsonRpc("/website_product_configurator/onchange", 'call', {
                form_values: form_data,
                field_name: $(this)[0].name,
            }).then(function(data) {
                if (data.error) {
                    openWarningDialog(data.error);
                } else {
                    var values = data.value;
                    var domains = data.domain;

                    var open_cfg_step_line_ids = data.open_cfg_step_line_ids;
                    var config_image_vals = data.config_image_vals;

                    _applyDomainOnValues(domains);
                    _handleOpenSteps(open_cfg_step_line_ids);
                    _setImageUrl(config_image_vals);
                    _setWeightPrice(values.weight, values.price, data.decimal_precision);
                };
            });
            _handleCustomAttribute(ev)
        });

        config_form.find('.custom_config_value.config_attachment').change(function (ev) {
            var file = ev.target.files[0];
            var loaded = false;
            var files_data = '';
            var BinaryReader = new FileReader();
            // file read as DataURL
            BinaryReader.readAsDataURL(file);
            BinaryReader.onloadend = function (upload) {
                var buffer = upload.target.result;
                buffer = buffer.split(',')[1];
                files_data = buffer;
                image_dict[ev.target.name]= files_data;
            }
        });

        function openWarningDialog(message) {
            var dialog = new Dialog(config_form, {
                title: "Warning!!!",
                size: 'medium',
                $content: "<div>" + message + "</div>",
            }).open();
        }

        function price_to_str(price, precision) {
            var l10n = _t.database.parameters;
            var formatted = _.str.sprintf('%.' + precision + 'f', price).split('.');
            formatted[0] = utils.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        };

        function weight_to_str(weight, precision) {
            var l10n = _t.database.parameters;
            var formatted = _.str.sprintf('%.' + precision + 'f', weight).split('.');
            formatted[0] = utils.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        };

        function _setWeightPrice(weight, price, decimal_precisions) {
            var formatted_price = price_to_str(price, decimal_precisions.price);
            var formatted_weight = weight_to_str(weight, decimal_precisions.weight);
            $('.config_product_weight').text(formatted_weight);
            $('.config_product_price').find('.oe_currency_value').text(formatted_price);
        };

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
            var custom_config_attr = $(event.currentTarget).find('.custom_config_attr_value');
            var flag_custom = false;
            if (custom_config_attr.length && custom_config_attr[0].tagName == "OPTION" && custom_config_attr[0].selected) {
                flag_custom = true;
            } else if (custom_config_attr.length && custom_config_attr[0].tagName == "INPUT" && custom_config_attr[0].checked) {
                flag_custom = true;
            };
            if (flag_custom && custom_value_container.hasClass('d-none')) {
                custom_value_container.removeClass('d-none');
                custom_value.addClass('required_config_attrib');
            } else if (!custom_value_container.hasClass('d-none')){
                custom_value_container.addClass('d-none');
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
                    if (!step.hasClass('d-none')) {
                        step.addClass('d-none');
                    };
                } else {
                    if (step.hasClass('d-none')) {
                        step.removeClass('d-none');
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
                    if (condition == 'in' || condition == '=') {
                        if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                            $(option).attr('disabled', true);
                            if (option.selected) {
                                option.selected = false;
                            } else if (option.checked) {
                                option.checked = false;
                            };
                        } else {
                            $(option).attr('disabled', false);
                        };
                    } else if (condition == 'not in' || condition == '!=') {
                        if ($.inArray(parseInt(option.value), domain[0][2]) < 0) {
                            $(option).attr('disabled', false);
                        } else {
                            $(option).attr('disabled', true);
                            if (option.selected) {
                                option.selected = false;
                            } else if (option.checked) {
                                option.checked = false;
                            };
                        };
                    };
                });
            });
        }

        function _onChangeConfigStep(event, next_step) {
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.show');
            var config_attr = active_step.find('.form-control.required_config_attrib');
            var flag = _checkRequiredFields(config_attr)
            var config_step_header = config_form.find('.nav.nav-tabs');
            var current_config_step = config_step_header.find('.nav-item.config_step > a.active').parent().attr('data-step-id');
            var form_data = config_form.serializeArray();
            for (var field_name in image_dict) {
                form_data.push({'name': field_name, 'value': image_dict[field_name]});
            }
            if (flag) {
                return ajax.jsonRpc("/website_product_configurator/save_configuration", 'call', {
                    form_values: form_data,
                    next_step: next_step || false,
                    current_step: current_config_step || false,
                }).then(function(data) {
                    if (data.error) {
                        openWarningDialog(data.error);
                    };
                    return data;
                });
            } else {
                return false;
            }
        };

        function _displayTooltip(config_attribute, message) {
            $(config_attribute).tooltip({
                title: message,
                placement: "bottom",
                trigger: "manual",
            }).tooltip('show');
            setTimeout(function(){
                $(config_attribute).tooltip('dispose');
            }, 4000);
        };

        function _checkRequiredFieldsRadio(parent_container) {
            var radio_inputs = parent_container.find('.config_attr_value:checked');
            if (radio_inputs.length) {
                return true;
            } else {
                return false;
            }
        }

        function _checkRequiredFields(config_attr) {
            var flag_all = true;
            for (var i = 0; i < config_attr.length; i++) {
                var flag = true;
                if (!$(config_attr[i]).hasClass('required_config_attrib')) {
                    flag = true;
                } else if (config_attr[i].tagName == 'FIELDSET') {
                    flag = _checkRequiredFieldsRadio($(config_attr[i]));
                } else if (!config_attr[i].value.trim()  || config_attr[i].value == '0') {
                    flag = false;
                };

                if (!flag) {
                    $(config_attr[i]).addClass('textbox-border-color');
                } else if (flag && $(config_attr[i]).hasClass('textbox-border-color')) {
                    $(config_attr[i]).removeClass('textbox-border-color');
                };
                flag_all &= flag;
            };
            return flag_all;
        };

        function _handleFooterButtons(step) {
            var step_count = step.attr('data-step-count');
            var total_steps = $('#total_attributes').val();
            if (step_count == '1') {
                $('.btnPreviousStep').addClass('d-none');
                $('.btnNextStep').removeClass('d-none');
                $('.configureProduct').addClass('d-none');
            } else if (step_count == total_steps) {
                $('.btnPreviousStep').removeClass('d-none');
                $('.btnNextStep').addClass('d-none');
                $('.configureProduct').removeClass('d-none');
            } else {
                $('.btnPreviousStep').removeClass('d-none');
                $('.btnNextStep').removeClass('d-none');
                $('.configureProduct').addClass('d-none');
            }
        }

        config_form.find('.config_attribute').change(function (event) {
            var attribute = [event.currentTarget];
            _checkRequiredFields(attribute);
        });

        config_form.find('.custom_config_value').change(function (event) {
            var attribute = [event.currentTarget];
            _checkRequiredFields(attribute);
        });

        config_form.find('.config_step').click(function (event) {
            var next_step = event.currentTarget.getAttribute('data-step-id');
            var result = _onChangeConfigStep(event, next_step);
            if (!result) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                _handleFooterButtons($(event.currentTarget))
            };
        });

        $('.btnNextStep').click(function(){
            $('.nav-tabs > .config_step > .active').parent().nextAll('li:not(.d-none):first').find('a').trigger('click');
        });

        $('.btnPreviousStep').click(function(){
            $('.nav-tabs > .config_step > .active').parent().prevAll('li:not(.d-none):first').find('a').trigger('click');
        });

        function _openNextStep(step) {
            var config_step_header = config_form.find('.nav.nav-tabs');
            var config_step = config_step_header.find('.nav-item.config_step > .nav-link.active');
            if (config_step.length) {
                config_step.removeClass('active');
            }
            var active_step = config_form.find('.tab-content').find('.tab-pane.active.show');
            active_step.removeClass('active');
            active_step.removeClass('show');

            var next_step = config_step_header.find('.nav-item.config_step[data-step-id=' + step + '] > .nav-link');
            if (next_step.length) {
                next_step.addClass('active');
                var selector = next_step.attr('href');
                var step_to_active = config_form.find('.tab-content').find(selector);
                step_to_active.addClass('active');
                step_to_active.addClass('show');
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

        // Radio button work with image click
        $('.image_config_attr_value_radio').on("click", function(event) {
            var val_id = $(this).data('val-id');
            var value_input = $(this).closest('fieldset').find('.config_attr_value[data-oe-id="' + val_id + '"]');
            if (value_input.prop('disabled')) {
                return
            }
            if (value_input.length) {
                if (value_input.attr('type') == 'checkbox' && value_input.prop('checked')) {
                    value_input.prop('checked', false);
                } else {
                    value_input.prop('checked', 'checked');
                }
                value_input.change();
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
            var custom_value = current_target.closest('.input-group').find('input.custom_config_value');
            var max_val = parseFloat(custom_value.attr('max') || Infinity);
            var min_val = parseFloat(custom_value.attr('min') || 0);
            var new_qty = min_val;
            var ui_val = parseFloat(custom_value.val());
            var custom_type = custom_value.attr('data-type');
            if (isNaN(ui_val)) {
                var message = "Please enter a number.";
                _displayTooltip(custom_value, message);
            } else if (custom_type == 'int' && ui_val % 1 !== 0) {
                var message = "Please enter a Integer.";
                _displayTooltip(custom_value, message);
            } else {
                var quantity = ui_val || 0;
                new_qty = quantity;
                if (current_target.has(".fa-minus").length) {
                    new_qty = quantity - 1;
                } else if (current_target.has(".fa-plus").length) {
                    new_qty = quantity + 1;
                }
                if (new_qty > max_val) {
                    var attribute_name = custom_value.closest('.tab-pane').find('label[data-oe-id="' + custom_value.attr('data-oe-id') + '"]');
                    var message = "Selected custom value " + attribute_name.text() + " must not be greater than " + max_val;
                    _displayTooltip(custom_value, message);
                    new_qty = max_val;
                }
                else if (new_qty < min_val) {
                    var attribute_name = custom_value.closest('.tab-pane').find('label[data-oe-id="' + custom_value.attr('data-oe-id') + '"]');
                    var message = "Selected custom value " + attribute_name.text() + " must be at least " + min_val;
                    _displayTooltip(custom_value, message);
                    new_qty = min_val;
                }
            }
            custom_value.val(new_qty);
            _disableEnableAddRemoveQtyButton(new_qty ,max_val ,min_val)
            return custom_value;
        }

        $('.custom_config_value.spinner_qty').change(function(ev) {
            _handleSppinerCustomValue(ev);
        });

        $('.js_add_qty').on('click', function(ev) {
            var custom_value = _handleSppinerCustomValue(ev);
            _checkRequiredFields(custom_value);
        });

        $('.js_remove_qty').on('click', function(ev) {
            var custom_value = _handleSppinerCustomValue(ev);
            _checkRequiredFields(custom_value);
        });
    });

})
