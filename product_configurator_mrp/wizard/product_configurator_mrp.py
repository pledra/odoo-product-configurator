from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


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

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        try:
            custom_vals = {
                l.attribute_id.id:
                    l.value or l.attachment_ids for l in self.custom_value_ids
            }
            variant = self.product_tmpl_id.create_get_variant(
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
            'res_id': self.order_id.id,
        }

        self.order_id.product_id = variant.id
        onchange_vals = self.order_id.product_id_change(variant.id).get(
            'value')
        if onchange_vals:
            onchange_vals.update(self._convert_to_write(onchange_vals))
            self.order_id.write(onchange_vals)
        self.unlink()
        return action
