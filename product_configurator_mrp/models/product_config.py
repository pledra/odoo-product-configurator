from openerp import api, fields, models


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    # Exclude subconfigurable products from standalone configuration
    product_tmpl_id = fields.Many2one(
        domain=[
            ('config_ok', '=', True),
            ('master_template', '=', True)
        ]
    )
    parent_id = fields.Many2one(
        comodel_name='product.config.session',
        readonly=True,
        ondelete='cascade',
        string='Parent Session'
    )
    child_ids = fields.One2many(
        comodel_name='product.config.session',
        inverse_name='parent_id',
        string='Session Lines',
        help='Child configuration sessions'
    )
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1,
    )

    # @api.model
    # def get_bom_line_vals(self):
    #     """Returns a list of bom values representing the subsessions"""
    #     line_vals = []

    #     for subsession in self.child_ids:
    #         if subsession.product_tmpl_id.config_ok:
    #             custom_vals = subsession._get_custom_vals_dict()
    #             subvariant = subsession.product_tmpl_id.create_get_variant(
    #                 subsession.value_ids.ids,
    #                 custom_values=custom_vals,
    #                 session=subsession
    #             )
    #         else:
    #             val_ids = subsession.value_ids.ids
    #             domain = [
    #                 ('product_tmpl_id', '=', subsession.product_tmpl_id.id)
    #             ]
    #             domain += [
    #                 ('attribute_value_ids', '=', vid) for vid in val_ids
    #             ]
    #             subvariant = self.env['product.product'].search(domain)[:1]
    #         if subvariant:
    #             line_vals.append((0, 0, {
    #                 'product_id': subvariant.id,
    #                 'product_qty': subsession.quantity
    #             }))
    #     return line_vals
