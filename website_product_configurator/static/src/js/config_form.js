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
            	debugger;
            });
		});
	 });

});