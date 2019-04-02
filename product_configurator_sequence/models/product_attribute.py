from odoo import fields, models, api


class ProductAttributeValueLine(models.Model):
    _inherit = 'product.attribute.value.line'
    _rec_name = 'sequence'

    @api.model
    def _default_sequence(self):
        product_tmpl_id = self.env.context.get(
            'default_product_tmpl_id',
            False
        )
        attribute_line = self.env['product.attribute.value.line'].search(
            [('product_tmpl_id', '=', product_tmpl_id)]).mapped('sequence')
        if attribute_line:
            sequence = max(attribute_line) + 1
        else:
            sequence = 1
        return sequence

    sequence = fields.Integer(string='Sequence', default=_default_sequence)
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

    @api.model
    def create(self, vals):
        res = super(ProductAttributeValueLine, self).create(vals)
        product_att_line = self.env['product.attribute.value.line'].search([
            ('sequence', '>=', res.sequence_copy),
            ('product_tmpl_id', '=', res.product_tmpl_id.id)
        ]) - res
        curr_seq = res.sequence_copy + 1
        for line in product_att_line:
            line.sequence = curr_seq
            curr_seq += 1
        return res
