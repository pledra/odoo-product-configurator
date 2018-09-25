from openerp import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_value_ids = fields.One2many(
        comodel_name='product.attribute.value.custom',
        inverse_name='product_id',
        related="product_id.value_custom_ids",
        string="Custom Values"
    )
    config_ok = fields.Boolean(
        related='product_id.config_ok',
        string="Configurable"
    )

    @api.multi
    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""

        # TODO: change wizard model to product.configurator.sale

        extra_vals = {
            'order_line_id': self.id,
            'product_id': self.product_id.id,
        }
        wizard_model = 'product.configurator'
        return self.product_id.product_tmpl_id.create_configurator_wizard(
            model_name=wizard_model, extra_vals=extra_vals, click_next=True)
