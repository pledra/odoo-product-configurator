from openerp import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    description = fields.Text(string='Description')

    @api.multi
    def reconfigure_product(self):
        """ Create and launch a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""

        # TODO: This does not work
        wizard_obj = self.env['product.configurator']
        wizard = False
        if self.product_id.product_tmpl_id.config_ok:

            wizard = wizard_obj.create({
                'product_tmpl_id': self.product_id.product_tmpl_id.id,
                'prodlot_id': self.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator',
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=wizard and wizard.id,
            ),
            'target': 'new',
            'res_id': wizard and wizard.id,
        }
