from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductConfigBomLine(models.Model):
    _name = 'product.config.session.line'

    cfg_session_id = fields.Many2one(
        comodel_name='product.config.session',
        name='Configuration Session',
        ondelete='cascade',
        required=True,
    )
    attr_val_id = fields.Many2one(
        comodel_name='product.attribute.value',
        name="Attribute Value",
        required=True
    )
    quantity = fields.Integer(
        name="Quantity",
        required=True,
        default=1
    )


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=1,
    )
    cfg_line_ids = fields.One2many(
        comodel_name='product.config.session.line',
        inverse_name='cfg_session_id',
        name='Configuration Lines'
    )

    @api.model
    def search_bom(self, product):
        """Search for a bom on the given variant with the given cfg_line_vals

            :param variant: Dictionary with the current {dynamic_field: val}

            :returns bom: found / created mrp.bom record.
        """

        product_ids = self.cfg_line_ids.mapped('attr_val_id.product_id').ids

        if not product_ids:
            return None

        # Get a list of boms that could potentially have the same content
        self._cr.execute("""
            SELECT bom_id
            FROM mrp_bom_line
            WHERE product_id IN %s
            AND bom_id IN (
                SELECT id
                FROM mrp_bom
                WHERE product_id = %s
            )
            GROUP BY bom_id
            HAVING COUNT(*) = %s;
        """, (tuple(product_ids), product.id, len(product_ids)))

        potential_bom_ids = [row[0] for row in self._cr.fetchall()]

        if not potential_bom_ids:
            return None

        # If any potential boms are found the result should be narrow enough
        # to read and filter server-side
        potential_boms = self.env['mrp.bom'].browse(potential_bom_ids)

        cfg_session_line_vals = {
            (l.attr_val_id.product_id.id, l.quantity)
            for l in self.cfg_line_ids if l.attr_val_id.product_id
        }

        for bom in potential_boms:
            bom_line_vals = {
                (l.product_id.id, l.product_qty) for l in bom.bom_line_ids
            }
            if bom_line_vals == cfg_session_line_vals:
                return bom
        return None

    @api.model
    def get_bom_vals(self, product):

        bom_line_vals = []

        for line in self.cfg_line_ids:
            if not line.attr_val_id.product_id:
                continue
            line_vals = {
                'product_id': line.attr_val_id.product_id.id,
                'product_qty': line.quantity
            }
            bom_line_vals.append((0, 0, line_vals))

        return {
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'code': 'CS%d' % self.id,
            'product_qty': 1,
            'bom_line_ids': bom_line_vals,
        }

    @api.model
    def create_update_bom(self, product):
        """Search for an existing bom on the variant and set the first
        sequence or create a new bom if search returns nothing.

            :param product: Dictionary with the current {dynamic_field: val}
            :param domains: Odoo domains restricting attribute values

            :returns bom: Found / created mrp.bom record.
        """

        if product.product_tmpl_id != self.product_tmpl_id:
            raise ValidationError(_(
                "Cannot create a bom for a variant that does not belong to "
                "the same template as set on the configuration session")
            )

        bom = self.search_bom(product)

        if bom:
            # Todo set sequence or set preffered bom attribute = true
            return bom

        bom_vals = self.get_bom_vals(product)

        if not bom_vals:
            return None

        bom = self.env['mrp.bom'].create(bom_vals)
        return bom

    @api.multi
    def create_get_variant(self, value_ids=None, custom_vals=None):
        """Create a new BOM (if needed) for the newly retrieved / created
        variant"""
        variant = super(ProductConfigSession, self).create_get_variant(
            value_ids=value_ids, custom_vals=custom_vals)
        self.create_update_bom(variant)
        return variant

    # @api.model
    # def search_variant(self, value_ids=None, custom_vals=None,
    #                    product_tmpl_id=None):
    #     """Enable a lookup for an existing bill of material on the returned
    #     variant(s) if any."""
    #     products = super(ProductConfigSession, self).search_variant(
    #         value_ids=value_ids, custom_vals=custom_vals,
    #         product_tmpl_id=product_tmpl_id
    #     )

    #     if products:
    #         Create or update
    #         self.create_update_bom(products)

    #     return products

    #     if not self.exists():
    #         return products

    #     bom_obj = self.env['mrp.bom']
    #     bom_line_vals = self.get_bom_line_vals()

    #     for product in products:
    #         # Iterate through the variants and compare the
    #         # generated BOM with the existing one
    #         product_bom = bom_obj.browse(bom_obj._bom_find(product=product))
    #         product_bom_l
    #         if not product_bom or len(product_bom.bom_line_ids) != len(bom_line_vals):
    #             variants -= variant
    #             continue
    #         for line in bom_line_vals:
    #             bom_line = bom.bom_line_ids.filtered(
    #                 lambda b:
    #                     b.product_id.id == line[2]['product_id'] and
    #                     b.product_qty == line[2]['product_qty']
    #             )
    #             if not bom_line:
    #                 variants -= variant
    #                 continue
    #     return variants

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
