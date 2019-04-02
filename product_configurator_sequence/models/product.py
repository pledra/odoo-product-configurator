from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_configure_image(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.attribute.value.line',
            'name': "Configure Image",
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': dict(
                self.env.context,
                default_product_tmpl_id=self.id,
            ),
        }



