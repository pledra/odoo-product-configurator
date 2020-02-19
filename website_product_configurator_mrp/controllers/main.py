from odoo.http import request
from odoo import http

from odoo.addons.website_product_configurator.controllers.main import ProductConfigWebsiteSale



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
        if kw.get('assembly') == 'kit':
            product = request.env['product.product'].browse(int(product_id))
            attr_products = product.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            for product in attr_products.mapped('product_id'):
                request.website.sale_get_order(force_create=1)._cart_update(
                    product_id=int(product.id),
                    add_qty=add_qty,
                    set_qty=set_qty,
                    config_session_id=kw.get("config_session_id", False)
                )
        else:
            product = request.env['product.product'].browse(int(product_id))
            attr_products = product.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            request.website.sale_get_order(force_create=1)._cart_update(
                product_id=int(product.id),
                add_qty=add_qty,
                set_qty=set_qty,
                config_session_id=kw.get("config_session_id", False)
            )
        return request.redirect("/shop/cart")

    def config_vars(self, product_tmpl, active_step=None, data=None):
        res = super(WebsiteProductConfigMrp, self).config_vars(
            product_tmpl=product_tmpl, active_step=active_step, data=data)
        active_step = res.get('active_step')
        if active_step and active_step.product_tmpl_id != product_tmpl:
            pass
        return res
