from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        related="config_session_id.custom_value_ids",
        string="Custom Values",
    )
    config_ok = fields.Boolean(
        related="product_id.config_ok", string="Configurable", readonly=True
    )

    allow_configuration = fields.Boolean(
        related="picking_id.allow_configuration", string="Allow configuration"
    )
    config_session_id = fields.Many2one(
        comodel_name="product.config.session", string="Config Session"
    )

    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""
        wizard_model = "product.configurator.picking"

        extra_vals = {
            "picking_id": self.picking_id.id,
            "stock_move_id": self.id,
            "product_id": self.product_id.id,
        }
        self = self.with_context(
            {
                "default_picking_id": self.picking_id.id,
                "default_stock_move_id": self.id,
            }
        )
        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )
