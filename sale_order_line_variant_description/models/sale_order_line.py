# -*- coding: utf-8 -*-
# Copyright 2015-17 Alex Comba - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang)
            if product.variant_description_sale:
                self.name = product.variant_description_sale
        return res
