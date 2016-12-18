odoo.define('website_product_configurator.website_form', function (require) {
"use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var base = require('web_editor.base');
    var session = require('web.session');

    var path = window.location.pathname;
    var config_form = $("#product_config_form");

    $('button.cfg_clear').on('click', function(event){
        var path = window.location.pathname;
        ajax.jsonRpc(path + "/config_clear", 'call', {}).then(
            function (res) {
                if (res) {
                    window.location.replace(res)
                }
        });
    });

    function get_cfg_vals() {
        var cfg_vals = {};
        var inputs = config_form.find('.cfg_input');

        inputs.each(function(){
            var value = parseInt($(this).val());
            cfg_vals[$(this).attr('name')] = parseInt($(this).val())
        });

        return cfg_vals;
    };

    function update_config_image(cfg_vals) {
        ajax.jsonRpc(path + "/image_update", 'call', {'cfg_vals': cfg_vals}).then(
            function (res) {
                if (res) {
                    $('#cfg_image').attr('src', res);
                }
        });
    };

    function update_price(onchange_vals) {
        var dom_prices = $('#cfg_price_tags')
        dom_prices.text('');
        $('#cfg_tax').text(onchange_vals['prices']['taxes']);
        $('#cfg_total').text(onchange_vals['prices']['total']);
        var price_labels = $.map(onchange_vals['prices']['vals'], function(value, i) {
            var price = $('<span>').text(value[2] + ' ');
            var currency = $('<span>').text(onchange_vals['prices']['currency']);
            var cfg_price_div = $('<div>').addClass('col-sm-8 text-right');

            cfg_price_div.append($('<div>').addClass('label label-info').text(
                value[0] + ': ' + value[1]));

            dom_prices.append(cfg_price_div);
            dom_prices.append($('<div>').addClass('col-sm-4 text-right').append(price, currency));
            dom_prices.append($('<div>').addClass('clearfix'));
        });
    }


    function value_onchange(cfg_vals) {
        /* Show/hide available values with the configuration present in frontend passed as cfg_vals */
        ajax.jsonRpc(path + "/value_onchange", 'call', {'cfg_vals': cfg_vals}).then(
                function (res) {
                    if (res) {
                        var select_fields = config_form.find('select.cfg_input');
                        if (select_fields) {
                            var options = select_fields.children('option').not(':empty,[value="custom"]');
                            options.addClass('hidden');
                            var available_options = options.filter('[value="' + res['value_ids'].join('"],[value="') + '"]');
                            var unavailable_options = options.not(available_options).get();
                            $(unavailable_options).prop('selected', false);
                            available_options.removeClass('hidden');

                            select_fields.each(function(){
                                var select_options = $(this).children('option').not(':empty,.hidden');
                                $(this).prop('disabled', select_options.length ? false : true);
                            })

                        }
                        config_form.find('.cfg_input').each(function(){
                            update_price(res);
                        });
                    }
            });
    };

    /* Show custom input and when option is picked in selection field */

    config_form.on('change', '.cfg_input, .custom_val:not([type="file"])', onchange);

    /*TODO* Only when value is changed in custom value trigger not on every blur*/

    function onchange(){
        var cfg_input = $(this);
        var cfg_vals = config_form.find('.cfg_input, .custom_val').serializeArray();
        var custom_input = config_form.find('#custom_attribute_' + cfg_input.data('oe-id'));
        var value = cfg_input.val();

        /* Send all values from the form to backend */
        value_onchange(cfg_vals);

        if (cfg_input.is(':checked')) {
            if (cfg_input.attr('type') == 'radio') {
                var radio_inputs = config_form.find("input[name='" + cfg_input.attr('name') + "']")
                radio_inputs.each(function(){
                    if ($(this) != cfg_input) {
                        $(this).parent().removeClass('active');
                    }
                });
            }
            cfg_input.parent().addClass('active');
        }
        else {
            $(this).parent().removeClass('active');
        }

        if (custom_input && value == 'custom'){
            custom_input.attr('readonly', false);
            custom_input.closest('div.cfg_custom').removeClass('hidden');
        }
        else {
            custom_input.attr('readonly', 'readonly');
            custom_input.closest('div.cfg_custom').addClass('hidden')
            if (cfg_vals && $(this).hasClass('cfg_img_update')){
                update_config_image(cfg_vals);
            }
        }
    };

    //Show attribute tooltip on mouseover
    $('.cfg_tooltip').hover(function(){
            // Hover over code
            var title = $(this).attr('title');
            $(this).data('tipText', title).removeAttr('title');
            $('<p class="attr_description"></p>')
            .text(title)
            .appendTo('body')
            .fadeIn('slow');
    }, function() {
            // Hover out code
            $(this).attr('title', $(this).data('tipText'));
            $('.attr_description').remove();
    }).mousemove(function(e) {
            var mousex = e.pageX + 20; //Get X coordinates
            var mousey = e.pageY + 10; //Get Y coordinates
            $('.attr_description')
            .css({ top: mousey, left: mousex })
    });

    /* Validate the form */
    if (config_form) {
        config_form.validate({
            errorPlacement: function(error, element) {
                if (element.hasClass("custom_val")) {
                    error.insertAfter(element.parent());
                }
                else {
                    error.insertAfter(element);
                }
            }
        });
    }

    config_form.on('click', 'a.js_add_qty', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().parent().find("input");
        var min = parseFloat($input.data("min") || $input.attr("min") || 0);
        var max = parseFloat($input.data("max") || $input.attr("max") || Infinity);
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + parseFloat($input.val(),10);
        $input.val(quantity > min ? (quantity < max ? quantity : max) : min);
        $('input[name="'+$input.attr("name")+'"]').val(quantity > min ? (quantity < max ? quantity : max) : min);
        $input.change();
        return false;
    });

});
