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
        if product.config_ok and kw.get("assembly") == "kit":
            attr_value_ids = product.product_template_attribute_value_ids
            attr_products = attr_value_ids.mapped(
                "product_attribute_value_id.product_id"
            )
            if not attr_products:
                return super(WebsiteProductConfigMrp, self).cart_update(
                    product_id=product_id,
                    add_qty=add_qty, set_qty=set_qty, **kw
                )

            for product_id in attr_products:
                res = super(ProductConfigWebsiteSale, self).cart_update(
                    product_id=product_id,
                    add_qty=add_qty, set_qty=set_qty, **kw
                )
            return res
        else:
            return super(WebsiteProductConfigMrp, self).cart_update(
                product_id=product_id,
                add_qty=add_qty, set_qty=set_qty, **kw
            )
