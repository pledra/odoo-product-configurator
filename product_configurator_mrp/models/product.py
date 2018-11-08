# from mako.runtime import Context
# from odoo import api, models


# class ProductProduct(models.Model):
#     _inherit = 'product.product'

#     @api.model
#     def get_mako_cfg_parts(self, bom, cfg_parts=None):
#         """Attempt to return the configuration mapping of all variant
#            components
#         of this parent template"""
#         # TODO: Only from the bom line we cannot determine to what
#         attribute or
#         # subproduct this product is related to. The information is lost
#         if not cfg_parts:
#             cfg_parts = {}
#         bom_lines = bom.bom_line_ids
#         if not bom_lines:
#             return cfg_parts
#         for step in self.product_tmpl_id.config_step_line_ids:
#             attr_lines = step.attribute_line_ids
#             for attr_val in attr_lines.mapped('value_ids'):
#                 bom_line = bom_lines.filtered(
#                     lambda b: b.product_id == attr_val.product_id
#                 )
#                 if not bom_line:
#                     continue
#                 if step not in cfg_parts:
#                     cfg_parts[step] = []
#                 attr = attr_val.attribute_id
#                 cfg_parts[step].append({
#                     'attribute': attr,
#                     'quantity': bom_line.product_qty,
#                     'attribute_value': attr_val,
#                     'price': attr_val.product_id.lst_price
#                 })
#             subproduct = step.config_subproduct_line_id.subproduct_id
#             bom_line = bom_lines.filtered(
#                 lambda l: l.product_id.product_tmpl_id == subproduct)
#             if not bom_line:
#                 continue
#             # cfg_parts[step].append({
#             #     'quantity': bom_line.product_qty,
#             #     'attribute_value': attr_val,
#             #     'price': subproduct.lst_price
#             # })
#         return cfg_parts

#     @api.model
#     def _get_mako_context(self, buf):
#         res = super(ProductProduct, self)._get_mako_context(buf=buf)
#         bom_obj = self.env['mrp.bom']
#         bom = bom_obj.browse(bom_obj._bom_find(product=self))
#         cfg_parts = self.get_mako_cfg_parts(bom)

#         ctx_vars = res.kwargs
#         ctx_vars.update(cfg_parts=cfg_parts, bom=bom)
#         res = Context(buf, **ctx_vars)
#         return res
