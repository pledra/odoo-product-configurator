# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductConfigurator(models.Model):
    _inherit = 'product.configurator'

    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        readonly=True,
    )

    @api.multi
    def action_config_done(self):
        """This fuction are copied from product_configurator_wizard.ProductConfigurator
           We only add one "if" required for purchase_order
           Parse values and execute final code before closing the wizard"""
        custom_vals = {
            l.attribute_id.id:
                l.value or l.attachment_ids for l in self.custom_value_ids
        }

        if self.product_id:
            remove_cv_links = map(lambda cv: (2, cv), self.product_id.value_custom_ids.ids)
            new_cv_links = self.product_id.product_tmpl_id.encode_custom_values(custom_vals)
            self.product_id.write({
                'attribute_value_ids': [(6, 0, self.value_ids.ids)],
                'value_custom_ids':  remove_cv_links + new_cv_links,
            })
            if self.order_line_id:
                self.order_line_id.write(self._extra_line_values(self.order_line_id.order_id,
                                                                 self.product_id,
                                                                 new=False))
            if self.purchase_order_line_id:
                self.purchase_order_line_id.write(self._extra_line_values(self.purchase_order_line_id.order_id,
                                                                 self.product_id,
                                                                 new=False))
            self.unlink()
            return
