from odoo import fields, models, api


class ProductAttributeWizard(models.TransientModel):
    _name = 'product.attribute.wizard'

    sequence_number = fields.Integer(
        string="Sequence Number")

    @api.multi
    def mass_sequences(self):
        record = self.env['product.attribute.value.line'].browse(
            self._context.get('active_ids'))
        product_att_line = self.env['product.attribute.value.line'].search([
            ('sequence', '>=', self.sequence_number)]) - record
        curr_seq = self.sequence_number
        for rec in record:
            rec.sequence = curr_seq + 1
            curr_seq += 1
        for line in product_att_line:
            line.sequence = curr_seq + 1
            curr_seq += 1

