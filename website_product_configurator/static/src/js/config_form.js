odoo.define('website_product_configurator.config_form', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var time = require('web.time');
    var utils = require('web.utils');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');
    var _t = core._t;

    publicWidget.registry.ProductConfigurator = publicWidget.Widget.extend({
        selector: '.product_configurator',
        events: {
            'change.datetimepicker #product_config_form .input-group.date': '_onChangeDateTime',
            'change #product_config_form .config_attribute': '_onChangeConfigAttribute',
            'change #product_config_form .custom_config_value.config_attachment': '_onChangeFile',
            'change #product_config_form .custom_config_value': '_onChangeCustomField',
            'click #product_config_form .config_step': '_onClickConfigStep',
            'click #product_config_form .btnNextStep': '_onClickBtnNext',
            'click #product_config_form .btnPreviousStep': '_onClickBtnPrevious',
            'submit #product_config_form': '_onSubmitConfigForm',
            'click #product_config_form .image_config_attr_value_radio': '_onClickRadioImage',
            'change #product_config_form .custom_config_value.spinner_qty': '_onChangeQtySpinner',
            'click #product_config_form .js_add_qty': '_onClickAddQty',
            'click #product_config_form .js_remove_qty': '_onClickRemoveQty',
        },

        init: function () {
            this._super.apply(this, arguments);
            // datetime picker (for custom field)
            if (!$.fn.datetimepicker) {
                ajax.loadJS("/web/static/lib/tempusdominus/tempusdominus.js");
            }
            this.config_form = $("#product_config_form");
            this.datetimepickers_options = {
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
            this.datepickers_options = $.extend(
                {},
                this.datetimepickers_options,
                {format: time.getLangDateFormat()}
            )

            // for file (custom field)
            this.image_dict = {}

            // Block UI
            this.blockui_opts = $.blockUI.defaults
            this.blockui_opts.baseZ = 2147483647;
            this.blockui_opts.css.border = '0';
            this.blockui_opts.css["background-color"] = '';
            this.blockui_opts.overlayCSS["opacity"] = '0.5';
            this.blockui_opts.message = '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/><br /></h2>'
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            this.$('.product_config_datetimepicker').parent().datetimepicker(
                this.datetimepickers_options
            );
            this.$('.product_config_datepicker').parent().datetimepicker(
                this.datepickers_options
            );
            return def;
        },

        _onChangeConfigAttribute: function(event) {
            var self = this;
            var attribute = [event.currentTarget];
            self._checkRequiredFields(attribute);
            var flag = self._checkChange(self);
            if (flag) {
                var form_data = self.config_form.serializeArray();
                for (var field_name in self.image_dict) {
                    form_data.push({'name': field_name, 'value': self.image_dict[field_name]});

                }
                $.blockUI(self.blockui_opts);
                    ajax.jsonRpc("/website_product_configurator/onchange", 'call', {
                        form_values: form_data,
                        field_name: attribute[0].getAttribute("name"),
                    }).then(function(data) {
                        if (data.error) {
                            self.openWarningDialog(data.error);
                        } else {
                            var values = data.value;
                            var domains = data.domain;

                            var open_cfg_step_line_ids = data.open_cfg_step_line_ids;
                            var config_image_vals = data.config_image_vals;

                            self._applyDomainOnValues(domains);
                            self._setDataOldValId();
                            self._handleOpenSteps(open_cfg_step_line_ids);
                            self._setImageUrl(config_image_vals);
                            self._setWeightPrice(values.weight, values.price, data.decimal_precision);
                        };
                        if ($.blockUI) {
                            $.unblockUI();
                        }
                    });
                    self._handleCustomAttribute(event)
            };
        },

        _checkChange: function (attr_field) {
            var flag = true
            if ($(attr_field).hasClass('cfg-radio')) {
                flag = !($(attr_field).attr('data-old-val-id') == $(attr_field).find('input:checked').val());
            } else if ($(attr_field).hasClass('cfg-select')) {
                flag = !($(attr_field).attr('data-old-val-id') == $(attr_field).val());
            }
            return flag
        },

        openWarningDialog: function (message) {
            var self = this;
            var dialog = new Dialog(self.config_form, {
                title: "Warning!!!",
                size: 'medium',
                $content: "<div>" + message + "</div>",
            }).open();
        },

        _applyDomainOnValues: function (domains) {
            var self = this;
            _.each(domains, function (domain, attr_id) {
                var $selection = self.config_form.find('#' + attr_id);
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
                if (!domain[0][2].length && $selection.attr('data-attr-required') && $selection.hasClass('required_config_attrib')) {
                    $selection.removeClass('required_config_attrib');
                    $selection.removeClass('textbox-border-color');
                } else if (domain[0][2].length &&
                    !$selection.hasClass('required_config_attrib') &&
                    $selection.attr('data-attr-required')
                ) {
                    $selection.addClass('required_config_attrib');
                }
            });
        },

        _setDataOldValId: function () {
            var selections = $('.cfg-select.config_attribute')
            _.each(selections, function (select) {
                $(select).attr('data-old-val-id', $(select).val());
            })
            var fieldsets = $('.cfg-radio.config_attribute')
            _.each(fieldsets, function (fieldset) {
                $(fieldset).attr('data-old-val-id', $(fieldset).find('input:checked').val() || '');
            })
        },

        _handleOpenSteps: function (open_cfg_step_line_ids) {
            var self = this;
            var $steps = self.config_form.find('.config_step');
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
        },

        _setImageUrl: function (config_image_vals) {
            var images = '';
            if (config_image_vals){
                var model = config_image_vals.name
                config_image_vals.config_image_ids.forEach(function(line){
                    images += "<img itemprop='image' class='cfg_image img img-responsive pull-right'"
                    images += "src='/web/image/"+model+"/"+line+"/image_1920'/>"
                })
            }
            if (images) {
                $('#product_config_image').html(images);
            }
        },

        price_to_str: function (price, precision) {
            var l10n = _t.database.parameters;
            var formatted = _.str.sprintf('%.' + precision + 'f', price).split('.');
            formatted[0] = utils.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        },

        weight_to_str: function (weight, precision) {
            var l10n = _t.database.parameters;
            var formatted = _.str.sprintf('%.' + precision + 'f', weight).split('.');
            formatted[0] = utils.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        },

        _setWeightPrice: function (weight, price, decimal_precisions) {
            var self = this;
            var formatted_price = self.price_to_str(price, decimal_precisions.price);
            var formatted_weight = self.weight_to_str(weight, decimal_precisions.weight);
            $('.config_product_weight').text(formatted_weight);
            $('.config_product_price').find('.oe_currency_value').text(formatted_price);
        },

        _handleCustomAttribute: function (event) {
            var container = $(event.currentTarget).closest('.tab-pane.container');
            var attribute_id = $(event.currentTarget).attr('data-oe-id');
            var custom_value = container.find('.custom_config_value[data-oe-id=' + attribute_id + ']');
            var custom_value_container = custom_value.closest('.custom_field_container[data-oe-id=' + attribute_id + ']');
            var attr_field = container.find('.config_attribute[data-oe-id=' + attribute_id + ']');
            var custom_config_attr = attr_field.find('.custom_config_attr_value');
            var flag_custom = false;
            if (custom_config_attr.length && custom_config_attr[0].tagName == "OPTION" && custom_config_attr[0].selected) {
                flag_custom = true;
            } else if (custom_config_attr.length && custom_config_attr[0].tagName == "INPUT" && custom_config_attr[0].checked) {
                flag_custom = true;
            };
            if (flag_custom && custom_value_container.hasClass('d-none')) {
                custom_value_container.removeClass('d-none');
                custom_value.addClass('required_config_attrib');
            } else if (!flag_custom && !custom_value_container.hasClass('d-none')){
                custom_value_container.addClass('d-none');
                if (custom_value.hasClass('required_config_attrib')) {
                    custom_value.removeClass('required_config_attrib');
                }
            }
        },

        _onChangeDateTime: function (event) {
            var self = this;
            var attribute = $(event.currentTarget).find('input.required_config_attrib');
            self._checkRequiredFields(attribute);
        },

        _checkRequiredFields: function (config_attr) {
            var self = this;
            var flag_all = true;
            for (var i = 0; i < config_attr.length; i++) {
                var flag = true;
                if (!$(config_attr[i]).hasClass('required_config_attrib')) {
                    flag = true;
                } else if ($(config_attr[i]).hasClass('cfg-radio')) {
                    flag = self._checkRequiredFieldsRadio($(config_attr[i]));
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
        },

        _checkRequiredFieldsRadio: function (parent_container) {
            var radio_inputs = parent_container.find('.config_attr_value:checked');
            if (radio_inputs.length) {
                return true;
            } else {
                return false;
            }
        },

        _onChangeFile: function (ev) {
            var self = this;
            var result = $.Deferred();
            var file = ev.target.files[0];
            if (!file) {
                return true;
            }
            var loaded = false;
            var files_data = '';
            var BinaryReader = new FileReader();
            // file read as DataURL
            BinaryReader.readAsDataURL(file);
            BinaryReader.onloadend = function (upload) {
                var buffer = upload.target.result;
                buffer = buffer.split(',')[1];
                files_data = buffer;
                self.image_dict[ev.target.name]= files_data;
                result.resolve();
            }
            return result.promise();
        },

        _onChangeCustomField: function(event) {
            var self = this;
            var attribute = [event.currentTarget];
            self._checkRequiredFields(attribute);
        },

        _onClickConfigStep: function (event) {
            var self = this;
            var next_step = event.currentTarget.getAttribute('data-step-id');
            var result = self._onChangeConfigStep(event, next_step, true);
            if (!result) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                self._handleFooterButtons($(event.currentTarget))
            };
        },

        _onChangeConfigStep: function (event, next_step, check_change) {
            var self = this;
            var active_step = self.config_form.find('.tab-content').find('.tab-pane.active.show');
            var config_attr = active_step.find('.form-control.required_config_attrib');
            var flag = self._checkRequiredFields(config_attr)
            var config_step_header = self.config_form.find('.nav.nav-tabs');
            var current_config_step = config_step_header.find('.nav-item.config_step > a.active').parent().attr('data-step-id');
            var form_data = self.config_form.serializeArray();
            for (var field_name in self.image_dict) {
                form_data.push({'name': field_name, 'value': self.image_dict[field_name]});
            }
            if (flag){
                $.blockUI(self.blockui_opts);
                return ajax.jsonRpc("/website_product_configurator/save_configuration", 'call', {
                    form_values: form_data,
                    next_step: next_step || false,
                    current_step: current_config_step || false,
                    submit_configuration: event.type == 'submit'? true: false,
                }).then(function(data) {
                    if (data.error) {
                        self.openWarningDialog(data.error);
                    };
                    if ($.blockUI) {
                        $.unblockUI();
                    }

                    return data;
                });
            }else {
                return false;
            }
        },

        _handleFooterButtons: function (step) {
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
        },

        _onClickBtnNext: function (ev) {
            $('.nav-tabs > .config_step > .active').parent().nextAll('li:not(.d-none):first').find('a').trigger('click');
        },

        _onClickBtnPrevious: function (ev) {
            $('.nav-tabs > .config_step > .active').parent().prevAll('li:not(.d-none):first').find('a').trigger('click');
        },

        _onSubmitConfigForm: function (event) {
            var self = this;
            event.preventDefault();
            event.stopPropagation();

            var result = self._onChangeConfigStep(event, false);
            if (result) {
                result.then(function (data) {
                    if (data) {
                        if (data.next_step) {
                            self._openNextStep(data.next_step);
                        };
                        if (data.redirect_url) {
                            window.location = data.redirect_url;
                        };
                    };
                });
            }
        },

        _openNextStep: function (step) {
            var self = this;
            var config_step_header = self.config_form.find('.nav.nav-tabs');
            var config_step = config_step_header.find('.nav-item.config_step > .nav-link.active');
            if (config_step.length) {
                config_step.removeClass('active');
            }
            var active_step = self.config_form.find('.tab-content').find('.tab-pane.active.show');
            active_step.removeClass('active');
            active_step.removeClass('show');

            var next_step = config_step_header.find('.nav-item.config_step[data-step-id=' + step + '] > .nav-link');
            if (next_step.length) {
                next_step.addClass('active');
                var selector = next_step.attr('href');
                var step_to_active = self.config_form.find('.tab-content').find(selector);
                step_to_active.addClass('active');
                step_to_active.addClass('show');
            }
        },

        _onClickRadioImage: function(event) {
            var val_id = $(event.currentTarget).data('val-id');
            var value_input = $(event.currentTarget).closest('.cfg-radio').find('.config_attr_value[data-oe-id="' + val_id + '"]');
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
        },

        addRequiredAttr: function (config_step) {
            config_step = this.config_form.find('.tab-content').find('tab-pane container[data-step-id=' + config_step + ']');
            _.each(config_step.find('.form-control.config_attribute'), function(attribute_field) {
                $(attribute_field).attr('required', true);
            });
        },

        _onChangeQtySpinner: function (ev) {
            this._handleSppinerCustomValue(ev);
        },

        _onClickAddQty: function(ev) {
            var custom_value = this._handleSppinerCustomValue(ev);
            this._checkRequiredFields(custom_value);
        },

        _onClickRemoveQty: function(ev) {
            var custom_value = this._handleSppinerCustomValue(ev);
            this._checkRequiredFields(custom_value);
        },

        _handleSppinerCustomValue: function (ev) {
            var self = this;
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
                self._displayTooltip(custom_value, message);
            } else if (custom_type == 'int' && ui_val % 1 !== 0) {
                var message = "Please enter a Integer.";
                self._displayTooltip(custom_value, message);
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
                    self._displayTooltip(custom_value, message);
                    new_qty = max_val;
                }
                else if (new_qty < min_val) {
                    var attribute_name = custom_value.closest('.tab-pane').find('label[data-oe-id="' + custom_value.attr('data-oe-id') + '"]');
                    var message = "Selected custom value " + attribute_name.text() + " must be at least " + min_val;
                    self._displayTooltip(custom_value, message);
                    new_qty = min_val;
                }
            }
            custom_value.val(new_qty);
            self._disableEnableAddRemoveQtyButton(current_target, new_qty ,max_val ,min_val)
            return custom_value;
        },

        _displayTooltip: function (config_attribute, message) {
            $(config_attribute).tooltip({
                title: message,
                placement: "bottom",
                trigger: "manual",
            }).tooltip('show');
            setTimeout(function(){
                $(config_attribute).tooltip('dispose');
            }, 4000);
        },

        _disableEnableAddRemoveQtyButton: function (current_target, quantity, max_val, min_val) {
            var container = current_target.closest('.custom_field_container')
            if (quantity >= max_val) {
                container.find('.js_add_qty').addClass('btn-disabled');
            } else if (quantity < max_val && $('.js_add_qty').hasClass('btn-disabled')) {
                container.find('.js_add_qty').removeClass('btn-disabled');
            }
            if (quantity <= min_val) {
                container.find('.js_remove_qty').addClass('btn-disabled');
            } else if (quantity > min_val && $('.js_remove_qty').hasClass('btn-disabled')) {
                container.find('.js_remove_qty').removeClass('btn-disabled');
            }
        },

    })
    return publicWidget.registry.ProductConfigurator

})
