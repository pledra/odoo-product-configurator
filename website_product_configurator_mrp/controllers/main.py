# -*- coding: utf-8 -*-

from openerp.http import request

from openerp.addons.website_product_configurator.controllers.main import (
    WebsiteProductConfig
)


class WebsiteProductConfigMrp(WebsiteProductConfig):

    def cart_update(self, product, post):
        if post.get('assembly') == 'kit':
            attr_products = product.attribute_value_ids.mapped(
                'product_id')
            for product in attr_products:
                request.website.sale_get_order(force_create=1)._cart_update(
                    product_id=int(product.id),
                    add_qty=float(post.get('add_qty')),
                )
        else:
            request.website.sale_get_order(force_create=1)._cart_update(
                    product_id=int(product.id),
                    add_qty=float(post.get('add_qty')),
                )
        return request.redirect("/shop/cart")
