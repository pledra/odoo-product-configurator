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
    # def add_dynamic_fields(self, res, dynamic_fields, wiz):
    #     subattr_qty_prefix = self._prefixes.get('subattr_qty_prefix')
    # qty_field = subattr_qty_prefix + str(subproduct.id)
    #         if qty_field in fields:
    #             node = etree.Element(
    #                 "field",
    #                 name=qty_field,
    #                 on_change=onchange_str % field_name,
    #                 required='True'
    #             )
    #             orm.setup_modifiers(node)
    #             subproduct_config_group.append(node)

    # @api.multi
    # def write(self, vals):
    #     field_prefix = self._prefixes.get('field_prefix')
    #     attr_qty_prefix = self._prefixes.get('attr_qty_prefix')
    #             attr_val_variant_qty_fields = {
    #         k: v for k, v in vals.items()
    #         if k.startswith(attr_qty_prefix)
    #     }

    #     for qty_field, qty in attr_val_variant_qty_fields.items():
    #         if not qty:
    #             continue
    #         attr_id = int(qty_field.replace(attr_qty_prefix, ''))
    #         value_id = vals.get(field_prefix + str(attr_id))
    #         if value_id:
    #             attr_val = self.env['product.attribute.value'].browse(value_id)
    #         else:
    #             attr_val = self.value_ids.filtered(
    #                 lambda v: v.attribute_id.id == attr_id)

    #         subtmpls = self.child_ids.mapped('product_tmpl_id')
    #         product = attr_val[0].product_id
    #         product_tmpl = product.product_tmpl_id

    #         if len(attr_val) == 1 and product and product_tmpl not in subtmpls:
    #             self.env['product.config.session'].create({
    #                 'parent_id': self.config_session_id.id,
    #                 'product_tmpl_id': attr_val.product_id.product_tmpl_id.id,
    #                 'value_ids': attr_val.product_id.attribute_value_ids.ids,
    #                 'state': 'done',
    #                 'user_id': self.env.uid,
    #             })
    #         vals.get(qty_field)