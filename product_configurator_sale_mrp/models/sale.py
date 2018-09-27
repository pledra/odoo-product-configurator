from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        readonly=True
    )
