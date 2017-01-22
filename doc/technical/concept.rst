*******
Concept
*******

.. image:: images/configuration-process-diagram.png
    :align: center
    :alt: alternate text

Configurable Template (product.template)
----------------------------------------

Product Templates with the boolean config_ok field checked become Configurable Templates.

When config_ok is True the template does not generate variants automatically anymore.

The attributes set on the template are only mere instructions for a configurator to generate a user
friendly interface.

Configuration interfaces
------------------------

In order to give control to the user on the options he can pick we must generate a user friendly interface.

We have provided at the time of this writing two configuration interfaces: The Backend Wizard and Website / Ecommerce Configurator.

These interfaces read data from the configurable templates (Attributes, Values, Configuration Restrictions / Steps / Images etc).

Using this information we are able to generate an interface that allows the user to select the available options on the product.

We also have quite a few handy helper methods on the product.template to operate a configuration interface.

The most important part is enforcing restrictions so users cannot make mistakes and generate unbuildable variants.


Configuration Session (product.config.session)
----------------------------------------------

Whenever a user starts a configuration process, his selections must be saved in a session.

This way the user does not loose his progress when moving through multiple steps and he can also save his configuration.

Configuration sessions store the options selected by the user in either interface and validates them according to the restrictions applied on the product.template


Configurable Products (product.product)
---------------------------------------

Same as the product.template the configurable products or variants have a config_ok boolean field.

After a configuration session is valid and findal we can use the information form the session to generate a new product variant.


*********
Structure
*********

The logic is at the time of this writing divided between 3 modules:

	1. Product Configurator Base
		- This module holds the main methods required to build configuration interfaces, this includes:
			a. Prevention of automatically generated variants.
			b. Introduction of Required, Multi, Custom fields for attribute lines.
			c. Configuration restrictions or configuration rules.
			d. Configuration steps.
			e. Configuration images.
			f. Linking attribute values to product variants.
			g. Managing active configuration sessions for external configurators.
			h. Helper methods for creating, validating, searching configurable variants and more.
	2. Product Configurator Wizard
		- Based on the Product Configurator Base module it provides a native Odoo wizard with dynamically generated content.
		- Integrated with backend models such as sale.order, mrp.production etc. can directly create and edit configurable variants directy to the related lines of the model.
	3. Website Product Configurator
		- Provides a web based form in the front-end for users to generate variants fully integrated with the e-shop module.


**********************
product.template model
**********************

The product.template object has a boolean field 'config_ok' that is used to determine if it is a regular template product or a configurable one. This is the marker that activates all the related functionality, without it behavior of the original model remains completely unchanged.

Once this is checked the product.template:

	1. No longer generated variants automatically
	2. Has 3 extra fields on the attribute lines (Required, Multi, Custom) added by the base
	3. Shows the 'Configurator' tab reveiling configuration information also added by the base.



****************************
Website Product Configurator
****************************

As with all the website_* modules, most of the logic lies in the controllers (commonly located in module/controllers/). In our controller located at the aformentioned location in website_product_config/controllers/main.py we have our main class WebsiteProductConfig.

At the beginning of the class we define our two main routes used: cfg_tmpl_url, cfg_step_url. These can be changed by importing the class and overriding the properties with new values if one wishes to change the route.

****
Flow
****

action_configure()
==================

By accessing a configurable product using the routes above this is our first method that fires. It will run on every page load

The first job of this method is to generate a dictionary of values that will be later used in the qweb templated also known as updating the qwebcontext

	cfg_vars = self.config_vars(product_tmpl, active_step=config_step)

Next we redefine the post argument given by the standard Odoo http layer as this does not support 'multi' data (input radio with same name). So we parse the werkzeug post with a separate method in which we organize multiple values in a list.

	post = self.parse_config_post(product_tmpl)

A differentiation must be made between accessing a configurable product (or a different configuration step) or posting configuration data via the form. This is why we look for the POST method on the werkzeug httprequest **if request.httprequest.method == 'POST':**

Sanitization of data to prevent invalid / malicious input is done via config_parse. We will use only the output from this method to update configuration values

	parsed_vals = self.config_parse(product_tmpl, post, config_step)

If no errors were returned from the parsing method we can update the configuration for this user. This is used to retrieve the configuration values at a later time to pre-fill the values in the form. Also when the configuration is finished we can just create a new configurable variant using the validated and stored values.

The related product.config.session model is updated with the validated values from the frontend and can be uniquely identified using the unique session id.








