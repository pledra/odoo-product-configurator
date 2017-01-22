***********************************
Installing the Product Configurator
***********************************

In the rows below we will describe the process of installing the Product Configurator modules.

For this installation example we will assume that our Odoo server path will be available at *"~/odoo/9.0/server/"*. Keep in mind that any other location of your preference could be used.

1. Create the extra addons directory where the Product Configurator directory module will be placed:

    We recommend you to do it like so *"~/odoo/9.0/extra-addons/"*


2. Add the contents of the Product Configurator module in the newly created *"extra-addons"* directory:

    Adding your files here can be done in any way. For example you can do this by using the Github repository
    or if you recieved the files from Pledra, you can copy and paste them in the directory.

    The new directory path should look like this *"~/odoo/9.0/extra-addons/product-configurator"*


3. Let Odoo see that the Product Configurator module is added:

    In your server *".conf"* file on the *"addons_path"* line add the path to the Product Configurator module (*"/odoo/9.0/extra-addons/product-configurator"*).

    The addons path line should look like this *"addons_path = /odoo/9.0/server/openerp/addons,/odoo/9.0/server/addons,/odoo/9.0/extra-addons/product-configurator"*.


4. Make the Product configurator module available in your Odoo instance:

    Log in to Odoo using admin, enable the *Developer Mode* in the **About** box at the Admin panel which is located in the upper right corner, and in the **Apps** top menu select **Update Apps List**. Now Odoo should know about the Product configurator module.


5. Select the **Apps** menu at the top and, in the search bar in the top right, delete the default Apps filter and search for Product configurator. Click on its Install button and the installation will be concluded.

    If you want to install both the front-end and back-end Product configurator module you only have to install *"Website Product Configurator"*.


User access
------------

In order for users to have access to the Product Configurator module we must first grant it (for example employees need access).

1. Granting access to the Product Configurator is done like this:

    The Odoo *Developer mode* should be activated first.

    Then we navigate to **Settings** -> **Users** and click on the user we want do give access to.

    A new page is opened and on the *Technical Settings* section we check **Manage Product Variants** and **Manage Product Configurator**.

This will give users the ability to manage the Product Configurator module and use it's features.

