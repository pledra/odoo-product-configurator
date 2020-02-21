from odoo.http import request
from odoo import http

from odoo.addons.website_product_configurator.controllers.main import (
    ProductConfigWebsiteSale,
)


class WebsiteProductConfigMrp(ProductConfigWebsiteSale):
    @http.route(
        ["/shop/cart/update"],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        website=True,
        csrf=False,
    )
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        product = request.env["product.product"].browse(int(product_id))
        if product.config_ok:
            return super(WebsiteProductConfigMrp, self).cart_update(
                product_id=product_id,
                add_qty=add_qty, set_qty=set_qty, **kw
            )
        sale_order = request.website.sale_get_order(force_create=True)
        if kw.get("assembly") == "kit":
            attr_value_ids = product.product_template_attribute_value_ids
            attr_products = attr_value_ids.mapped(
                "product_attribute_value_id.product_id"
            )
            for product_id in attr_products:
                sale_order._cart_update(
                    product_id=int(product_id.id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    config_session_id=kw.get("config_session_id", False)
                )
        else:
            sale_order._cart_update(
                product_id=int(product.id),
                add_qty=add_qty,
                set_qty=set_qty,
                config_session_id=kw.get("config_session_id", False),
            )
        if kw.get("express"):
            return request.redirect("/shop/checkout?express=1")
        return request.redirect("/shop/cart")
