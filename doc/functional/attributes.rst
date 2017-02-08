**********
Attributes
**********

==========
Attributes
==========

Attributes in the Product Configurator have been enhanced a bit. Navigating to **Sales->Products->Attributes** we have the standard tree view. Creating a new attribute or clicking on an existing one now provides a form view.

**Required** and **Multi** fields serve as default values when adding this attribute to a configurable template in the attribute lines.

=============
Custom values
=============

After adding the attribute to a configurable template and clicking the Custom boolean field both the frotend and backend configurator will check the custom field type. Depending on field type set you can have more options and different behavior in the configuration interfaces.

**Integer** and **Float** values will permit a minimum and maximum value accepted for client-side and server-side validation

**Color** field type provides a color picker widget

**Searchable**: By default when a customer finishes configuration of a product, a search is made to see if there is such a product defined in the database already. This field determines if that search should include this custom value as well.

================
Attribute Values
================

Attribute values now have a link towards variants (product.product). Linking attribute values to products provides a large variety of benefits:

1. When selecting attributes in the frontend, the price of the related product is pulled and can offer a price for the selection as well as the final cost by adding everything up.

2. Images from the product variants can be used as thumbnails, it is a mandatory setup in order for the thumbnail view to work in the frontend.

3. Bom's can be computed by using all the related products from the attributes.