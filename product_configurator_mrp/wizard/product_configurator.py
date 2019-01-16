from odoo import models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    def get_onchange_vals(self, cfg_val_ids):
        vals = super(ProductConfigurator, self).get_onchange_vals(
            cfg_val_ids
        )
        weight = self.config_session_id.get_cfg_weight(value_ids=cfg_val_ids)
        vals.update(weight=weight)
        return vals
