# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProductConfigurator(models.TransientModel):

    _inherit = 'product.configurator'

    prodlot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        readonly=True
    )

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        if self._context.get('active_model', '') != 'stock.production.lot':
            return super(ProductConfigurator, self).action_config_done()
        custom_vals = {
            l.attribute_id.id:
                l.value or l.attachment_ids for l in self.custom_value_ids
        }

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
        except:
            raise ValidationError(
                _('Invalid configuration! Please check all '
                  'required steps and fields.')
            )
        prod_lot = self.env['stock.production.lot'].browse(
            self.env.context['active_id'])
        line_vals = {'product_id': variant.id}

        prod_lot.write(line_vals)

        self.unlink()
        return
