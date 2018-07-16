from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    master_template = fields.Boolean(
        string='Master Template',
        default=True,
        help="Indicates if this template can be configured as a "
             "stand-alone product or only as a sub-product",
    )
    config_subproduct_ids = fields.One2many(
        comodel_name='product.config.subproduct.line',
        inverse_name='product_tmpl_id',
        string='Configurable Subproducts',
        help="Define what other products are needed"
    )
