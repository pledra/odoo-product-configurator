# -*- coding: utf-8 -*-
from openerp.osv import orm
from openerp.addons.base.ir.ir_model import _get_fields_type

from openerp import models, fields, api, _
from openerp.exceptions import Warning, ValidationError


class FreeSelection(fields.Selection):

    def convert_to_cache(self, value, record, validate=True):
        return super(FreeSelection, self).convert_to_cache(
            value=value, record=record, validate=False)


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    order_line_id = fields.Many2one(comodel_name='sale.order.line',
                                    readonly=True)

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        if self._context.get('active_model', '') not in ('sale.order', 'sale.order.line'):
            return super(ProductConfigurator, self).action_config_done()
        custom_vals = {
            l.attribute_id.id:
                l.value or l.attachment_ids for l in self.custom_value_ids
        }

        # This try except is too generic.
        # The create_variant routine could effectively fail for
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

        so = self.env['sale.order'].browse(self.env.context.get('active_id'))

        line_vals = {'product_id': variant.id}
        line_vals.update(self._extra_line_values(
            self.order_line_id.order_id or so, variant, new=True)
        )

        if self.order_line_id:
            self.order_line_id.write(line_vals)
        else:
            so.write({'order_line': [(0, 0, line_vals)]})

        self.unlink()
        return
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
