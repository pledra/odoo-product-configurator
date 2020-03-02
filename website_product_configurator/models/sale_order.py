import logging
from odoo import api, models, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(
        self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs
    ):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault("lang", self.sudo().partner_id.lang)
        SaleOrderLineSudo = (
            self.env["sale.order.line"].sudo().with_context(product_context)
        )
        # change lang to get correct name of attributes/values
        product_with_context = self.env["product.product"].with_context(
            product_context
        )
        product = product_with_context.browse(int(product_id))

        if not product.product_tmpl_id.config_ok:
            return super(SaleOrder, self)._cart_update(
                product_id=product_id,
                line_id=line_id,
                add_qty=add_qty,
                set_qty=set_qty,
                kwargs=kwargs,
            )

        # Config session map
        config_session_id = kwargs.get("config_session_id", False)
        if not config_session_id and line_id:
            order_line = self._cart_find_product_line(
                product_id, line_id, **kwargs
            )[:1]
            config_session_id = order_line.config_session_id.id
        if config_session_id:
            config_session_id = int(config_session_id)
            if not product:
                config_session = self.env["product.config.session"].browse(
                    config_session_id
                )
                product = config_session.product_id
            session_map = ((product.id, config_session_id),)
            ctx = {
                "current_sale_line": line_id,
                "default_config_session_id": config_session_id,
                "product_sessions": session_map,
            }
            self = self.with_context(ctx)
            SaleOrderLineSudo = SaleOrderLineSudo.with_context(ctx)

        # Add to cart functionality
        try:
            if add_qty:
                add_qty = float(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = float(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != "draft":
            request.session["sale_order_id"] = None
            raise UserError(
                _(
                    "It is forbidden to modify a sales order "
                    "which is not in draft status."
                )
            )
        if line_id is not False:
            order_line = self._cart_find_product_line(
                product_id, line_id, **kwargs
            )[:1]

        # Create line if no line with product_id can be located
        if not order_line:
            if not product:
                raise UserError(
                    _(
                        "The given product does not exist therefore "
                        "it cannot be added to cart."
                    )
                )

            product_id = product.id
            values = self._website_product_id_change(
                self.id, product_id, qty=1
            )

            # create the line
            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                # The validation may occur in backend
                # eg: taxcloud) but should fail silently in frontend
                _logger.debug(
                    "ValidationError occurs during tax compute. %s" % (e)
                )
            if add_qty:
                add_qty -= 1

        # compute new quantity
        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)

        # Remove zero of negative lines
        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                # update description of the parent
                linked_product = product_with_context.browse(
                    linked_line.product_id.id
                )
                linked_line.name = linked_line.\
                    get_sale_order_line_multiline_description_sale(
                        linked_product
                    )
        else:
            # update line
            no_variant_attributes_price_extra = [
                ptav.price_extra
                for ptav in order_line.product_no_variant_attribute_value_ids
            ]
            values = self.with_context(
                no_variant_attributes_price_extra=tuple(
                    no_variant_attributes_price_extra
                )
            )._website_product_id_change(self.id, product_id, qty=quantity)
            if (
                self.pricelist_id.discount_policy == "with_discount"
                and not self.env.context.get("fixed_price")
            ):
                order = self.sudo().browse(self.id)
                product_context.update(
                    {
                        "partner": order.partner_id,
                        "quantity": quantity,
                        "date": order.date_order,
                        "pricelist": order.pricelist_id.id,
                        "force_company": order.company_id.id,
                    }
                )
                product_with_context = self.env[
                    "product.product"
                ].with_context(product_context)
                product = product_with_context.browse(product_id)
                values["price_unit"] = self.env[
                    "account.tax"
                ]._fix_tax_included_price_company(
                    order_line._get_display_price(product),
                    order_line.product_id.taxes_id,
                    order_line.tax_id,
                    self.company_id,
                )

            order_line.write(values)

            # link a product to the sales order
            if kwargs.get("linked_line_id"):
                linked_line = SaleOrderLineSudo.browse(
                    kwargs["linked_line_id"]
                )
                order_line.write({"linked_line_id": linked_line.id})
                linked_product = product_with_context.browse(
                    linked_line.product_id.id
                )
                linked_line.name = linked_line.\
                    get_sale_order_line_multiline_description_sale(
                        linked_product
                    )
            # Generate the description with everything. This is done after
            # creating because the following related fields have to be set:
            # - product_no_variant_attribute_value_ids
            # - product_custom_attribute_value_ids
            # - linked_line_id
            order_line.name = order_line.\
                get_sale_order_line_multiline_description_sale(
                    product
                )

        option_lines = self.order_line.filtered(
            lambda l: l.linked_line_id.id == order_line.id
        )

        return {
            "line_id": order_line.id,
            "quantity": quantity,
            "option_ids": list(set(option_lines.ids)),
        }

    def _website_product_id_change(self, order_id, product_id, qty=0):
        session_map = self.env.context.get("product_sessions", ())
        ctx = self._context.copy()
        if not session_map:
            current_sale_line = self.env.context.get("current_sale_line")
            sale_line = False
            if current_sale_line:
                sale_line = self.env["sale.order.line"].browse(
                    int(current_sale_line)
                )
            if sale_line:
                session_map = (
                    (sale_line.product_id.id, sale_line.cfg_session_id.id),
                )
            ctx["product_sessions"] = session_map
        if isinstance(session_map, tuple):
            session_map = dict(session_map)

        self = self.with_context(ctx)
        values = super(SaleOrder, self)._website_product_id_change(
            order_id=order_id, product_id=product_id, qty=qty
        )
        if session_map.get(product_id, False):
            config_session = self.env["product.config.session"].browse(
                session_map.get(product_id)
            )
            if not config_session.exists():
                return values
        return values

    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        """Include Config session in search.
        """
        order_line = super(SaleOrder, self)._cart_find_product_line(
            product_id=product_id, line_id=line_id, **kwargs
        )
        # Onchange quantity in cart
        if line_id:
            return order_line

        config_session_id = kwargs.get("config_session_id", False)
        if not config_session_id:
            session_map = self.env.context.get("product_sessions", ())
            if isinstance(session_map, tuple):
                session_map = dict(session_map)
            config_session_id = session_map.get(product_id, False)
        if not config_session_id:
            return order_line

        order_line = order_line.filtered(
            lambda p: p.config_session_id.id == int(config_session_id)
        )
        return order_line


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        return res

    @api.onchange(
        "product_id", "price_unit", "product_uom", "product_uom_qty", "tax_id"
    )
    def _onchange_discount(self):
        if self.config_session_id:
            self = self.with_context(
                product_sessions=(
                    (self.product_id.id, self.config_session_id.id),
                )
            )
        return super(SaleOrderLine, self)._onchange_discount()

    def _get_display_price(self, product):
        if self.config_session_id:
            session_map = ((self.product_id.id, self.config_session_id.id),)
            self = self.with_context(product_sessions=session_map)
            product = product.with_context(product_sessions=session_map)
        res = super(SaleOrderLine, self)._get_display_price(product=product)
        return res

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):
        if self.config_session_id:
            session_map = ((self.product_id.id, self.config_session_id.id),)
            self = self.with_context(product_sessions=session_map)
        super(SaleOrderLine, self).product_uom_change()

    def _get_real_price_currency(
        self, product, rule_id, qty, uom, pricelist_id
    ):
        if not product.config_ok:
            return super(SaleOrderLine, self)._get_real_price_currency(
                product=product,
                rule_id=rule_id,
                qty=qty,
                uom=uom,
                pricelist_id=pricelist_id,
            )
        currency_id = None
        product_currency = None
        if rule_id:
            PricelistItem = self.env["product.pricelist.item"]
            pricelist_item = PricelistItem.browse(rule_id)
            currency_id = pricelist_item.pricelist_id.currency_id
            if (
                pricelist_item.base == "pricelist"
                and pricelist_item.base_pricelist_id
            ):
                product_currency = pricelist_item.base_pricelist_id.currency_id
        product_currency = (
            product_currency
            or (product.company_id and product.company_id.currency_id)
            or self.env.user.company_id.currency_id
        )

        if not currency_id or currency_id.id == product_currency.id:
            currency_id = product_currency
        return product.price, currency_id
