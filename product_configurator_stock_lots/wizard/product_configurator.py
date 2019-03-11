from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProductConfiguratorLot(models.TransientModel):
    _name = 'product.configurator.lot'
    _inherit = 'product.configurator'

    prodlot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        readonly=True
    )

    @api.multi
    def action_next_step(self):
        """Run action_config_done for standard (non-configurable) products"""
        if not self.product_tmpl_id.config_ok:
            return self.action_config_done()
        return super(ProductConfiguratorLot, self).action_next_step()

    @api.multi
    def _extra_line_values(self, product):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""
        vals = {'product_id': product.id}
        if product.config_ok:
            description = product._get_mako_tmpl_name()
        else:
            description = product.display_name
        vals.update(description=description)
        return vals

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        if not self.product_tmpl_id.config_ok:
            variant = self.product_tmpl_id.product_variant_ids[0]
            line_vals = self._extra_line_values(variant)
            prod_lot = self.env['stock.production.lot'].create(line_vals)

            self.unlink()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.production.lot',
                'name': "Serial Number/Lot",
                'view_mode': 'form',
                'context': dict(
                    self.env.context,
                    custom_create_variant=True
                ),
                'res_id': prod_lot.id,
            }

        custom_vals = self.config_session_id._get_custom_vals_dict()
        # This try except is too generic.
        # The create_get_variant routine could effectively fail for
        # a large number of reasons, including bad programming.
        # It should be refactored.
        # In the meantime, at least make sure that a validation
        # error legitimately raised in a nested routine
        # is passed through.
        try:
            variant = self.product_tmpl_id.create_get_variant(
                self.value_ids.ids, custom_vals)
        except ValidationError:
            raise
        except Exception:
            raise ValidationError(
                _('Invalid configuration! Please check all '
                  'required steps and fields.')
            )
        line_vals = self._extra_line_values(variant)
        prod_lot = self.env['stock.production.lot'].create(line_vals)

        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.production.lot',
            'name': "Serial Number/Lot",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                custom_create_variant=True
            ),
            'res_id': prod_lot.id,
        }
