from odoo import api, models


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.multi
    def _get_matching_bom(self, product_id, values):
        moves = values.get('move_dest_ids')
        bom_id = moves[0].sale_line_id.bom_id if moves else None
        if bom_id:
            values.update(bom_id=bom_id)
        return super(ProcurementRule, self)._get_matching_bom(
            product_id=product_id, values=values
        )
