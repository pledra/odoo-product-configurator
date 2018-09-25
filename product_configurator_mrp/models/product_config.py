from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductConfigBomLine(models.Model):
    _name = 'product.config.bom.line'

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
    product_id = fields.Many2one(
        comodel_name='product.product',
        related='attr_val_id.product_id',
        required=True,
        readonly=True
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
    cfg_bom_line_ids = fields.One2many(
        comodel_name='product.config.bom.line',
        inverse_name='cfg_session_id',
        name='Configuration Lines'
    )

    @api.constrains('cfg_bom_line_ids')
    def check_lines(self):
        if any(not l.product_id for l in self.cfg_bom_line_ids):
            raise ValidationError(
                _('Config session lines must have attribute values with '
                  'related products only')
            )

    @api.model
    def search_bom(self, product):
        """Search for a bom on the given variant with the given cfg_line_vals

            :param variant: Dictionary with the current {dynamic_field: val}

            :returns bom: found / created mrp.bom record.
        """

        products = self.cfg_bom_line_ids.mapped('attr_val_id.product_id')
        product_cfg_lines = self.cfg_bom_line_ids.filtered(
            lambda l: l.product_id
        )
        total_qty = sum(product_cfg_lines.mapped('quantity'))

        if not product:
            return None

        # Get a list of boms that could potentially have the same content
        self._cr.execute("""
            SELECT bom_id
            FROM mrp_bom_line
            WHERE product_id IN %s
            AND bom_id IN (
                SELECT id
                FROM mrp_bom
                WHERE active = True
                AND product_id = %s
            )
            GROUP BY bom_id
            HAVING COUNT(*) = %s
            AND SUM(product_qty) = %s;
        """, (tuple(products.ids), product.id, len(products.ids), total_qty))

        potential_bom_ids = [row[0] for row in self._cr.fetchall()]

        if not potential_bom_ids:
            return None

        # If any potential boms are found the result should be narrow enough
        # to read and filter server-side
        potential_boms = self.env['mrp.bom'].browse(potential_bom_ids)

        cfg_session_line_vals = {
            (l.attr_val_id.product_id.id, l.quantity)
            for l in self.cfg_bom_line_ids if l.attr_val_id.product_id
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

        for line in self.cfg_bom_line_ids:
            if not line.product_id:
                continue
            line_vals = {
                'product_id': line.product_id.id,
                'product_qty': line.quantity
            }
            bom_line_vals.append((0, 0, line_vals))

        if not bom_line_vals:
            return None

        return {
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'code': self.name,
            'product_qty': 1,
            'bom_line_ids': bom_line_vals,
        }

    @api.model
    def create_get_bom(self, product):
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
        self.create_get_bom(variant)
        return variant
