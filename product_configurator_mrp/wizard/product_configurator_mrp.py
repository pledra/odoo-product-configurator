from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductConfiguratorMrp(models.TransientModel):
    _name = 'product.configurator.mrp'
    _inherit = 'product.configurator'

    order_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        required=True
    )

    @api.model
    def create(self, vals):
        order_id = self._context.get('default_order_id')
        if order_id:
            vals.update(order_id=int(order_id))
        return super(ProductConfiguratorMrp, self).create(vals)

    def _get_order_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""

        line_vals = {
            'product_id': product_id.id,
        }
        return line_vals

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        step_to_open = self.config_session_id.check_and_open_incomplete_step()
        if step_to_open:
            return self.open_step(step_to_open)
        try:
            custom_vals = {
                l.attribute_id.id:
                    l.value or l.attachment_ids for l in self.custom_value_ids
            }
            variant = self.config_session_id.create_get_variant(
                self.value_ids.ids, custom_vals)

        except ValidationError:
            raise
        except Exception:
            raise ValidationError(
                _('Invalid configuration! Please check all '
                  'required steps and fields.')
            )

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'name': "Manufacturing Order",
            'view_mode': 'form',
            'context': self.env.context,
            'res_id': variant.id,
        }

        line_vals = self._get_order_vals(variant)

        mrpProduction = self.env['mrp.production']
        specs = mrpProduction._onchange_spec()
        updates = mrpProduction.onchange(line_vals, ['product_id'], specs)
        values = updates.get('value', {})
        for name, val in values.items():
            if isinstance(val, tuple):
                values[name] = val[0]
        if values:
            line_vals.update(values)
            self.order_id.write(line_vals)
        self.unlink()
        return action
