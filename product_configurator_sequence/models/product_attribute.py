from odoo import fields, models, api


class ProductAttributeValueLine(models.Model):
    _inherit = 'product.attribute.value.line'

    sequence = fields.Integer(string='Sequence',
        default=lambda self: max(self.env['product.attribute.value.line'].search([]).mapped('sequence')) + 1)
    sequence_copy = fields.Integer(
        string='Sequence', related='sequence')

    @api.multi
    def add_after(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.attribute.value.line',
            'name': "Configure Image",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                default_sequence=self.sequence + 1,
            ),
        }
    