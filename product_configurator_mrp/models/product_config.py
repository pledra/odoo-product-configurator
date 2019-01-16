from odoo import api, fields, models


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    @api.model
    def get_cfg_weight(self, value_ids=None, custom_vals=None):
        """ Computes the weight of the configured product based on the configuration
            passed in via value_ids and custom_values

        :param value_ids: list of attribute value_ids
        :param custom_vals: dictionary of custom attribute values
        :returns: final configuration weight"""

        if not value_ids:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = {}

        product_tmpl = self.product_tmpl_id

        self = self.with_context({'active_id': product_tmpl.id})

        vals = self.env['product.attribute.value'].browse(value_ids)

        weight_extra = 0.0
        for attribute_price in vals.mapped('price_ids'):
            if attribute_price.product_tmpl_id == product_tmpl:
                weight_extra += attribute_price.weight_extra

        return product_tmpl.weight + weight_extra

    @api.multi
    def _compute_cfg_weight(self):
        for cfg_session in self:
            cfg_session.weight = cfg_session.get_cfg_weight()

    weight = fields.Float(
        string="Weight",
        compute="_compute_cfg_weight"
    )
