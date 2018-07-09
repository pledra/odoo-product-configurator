from mako.runtime import Context
from openerp import api, fields, models


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'

    quantity = fields.Boolean(
        string='Quantity',
        help='Set quantity for variants related to attribute values selected?'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_mako_cfg_parts(self, bom, cfg_parts=None):
        """Attempt to return the configuration mapping of all variant components
        of this parent template"""
        # TODO: Only from the bom line we cannot determine to what attribute or
        # subproduct this product is related to. The information is lost
        if not cfg_parts:
            cfg_parts = {}
        bom_lines = bom.bom_line_ids
        if not bom_lines:
            return cfg_parts
        for step in self.product_tmpl_id.config_step_line_ids:
            attr_lines = step.attribute_line_ids
            for attr_val in attr_lines.mapped('value_ids'):
                bom_line = bom_lines.filtered(
                    lambda b: b.product_id == attr_val.product_id
                )
                if not bom_line:
                    continue
                if step not in cfg_parts:
                    cfg_parts[step] = []
                attr = attr_val.attribute_id
                cfg_parts[step].append({
                    'attribute': attr,
                    'quantity': bom_line.product_qty,
                    'attribute_value': attr_val,
                    'price': attr_val.product_id.lst_price
                })
            subproduct = step.config_subproduct_line_id.subproduct_id
            bom_line = bom_lines.filtered(
                lambda l: l.product_id.product_tmpl_id == subproduct)
            if not bom_line:
                continue
            # cfg_parts[step].append({
            #     'quantity': bom_line.product_qty,
            #     'attribute_value': attr_val,
            #     'price': subproduct.lst_price
            # })
        return cfg_parts

    @api.model
    def _get_mako_context(self, buf):
        res = super(ProductProduct, self)._get_mako_context(buf=buf)
        bom_obj = self.env['mrp.bom']
        bom = bom_obj.browse(bom_obj._bom_find(product=self))
        cfg_parts = self.get_mako_cfg_parts(bom)

        ctx_vars = res.kwargs
        ctx_vars.update(cfg_parts=cfg_parts, bom=bom)
        res = Context(buf, **ctx_vars)
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing'
    )

    @api.multi
    def search_variant(self, value_ids, custom_values=None):
        variants = super(ProductTemplate, self).search_variant(
            value_ids, custom_values=custom_values
        )

        cfg_session_id = self._context.get('config_session_id')

        if not cfg_session_id:
            return variants

        session_obj = self.env['product.config.session']
        try:
            session = session_obj.browse(int(cfg_session_id))
        except:
            session = session_obj

        if not session.child_ids:
            return variants

        bom_obj = self.env['mrp.bom']

        bom_line_vals = session.get_bom_line_vals()

        for variant in variants:
            bom = bom_obj.browse(bom_obj._bom_find(product=variant))
            if not bom or len(bom.bom_line_ids) != len(bom_line_vals):
                variants -= variant
                continue
            for line in bom_line_vals:
                bom_line = bom.bom_line_ids.filtered(
                    lambda b:
                        b.product_id.id == line[2]['product_id'] and
                        b.product_qty == line[2]['product_qty']
                )
                if not bom_line:
                    variants -= variant
                    continue
        return variants[:1]

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None, session=None):
        """Add bill of matrials to the configured variant."""
        if not session:
            session = self.env['product.config.session'].search_session(
                product_tmpl_id=self.id)[:1]

        self = self.with_context(config_session_id=session.id)

        variant = super(ProductTemplate, self).create_get_variant(
            value_ids, custom_values=custom_values)

        bom_obj = self.env['mrp.bom']
        bom = bom_obj.browse(bom_obj._bom_find(product=variant))
        if not bom:
            bom_line_vals = session.get_bom_line_vals()
            if bom_line_vals:
                bom_obj.create({
                    'product_tmpl_id': self.id,
                    'product_id': variant.id,
                    'bom_line_ids': bom_line_vals,
                    'type': 'normal',
                    'routing_id': self.routing_id.id or False,
                })

        return variant
