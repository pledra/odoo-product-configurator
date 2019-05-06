from odoo import fields, models
import base64

from io import BytesIO
from PIL import Image


class ProductConfiguratorSession(models.Model):
    _inherit = 'product.config.session'

    @api.multi
    def action_config_done(self, value_ids=False, custom_value_ids=False):
        """Parse values and execute final code before closing the wizard"""

        if not value_ids
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
