# -*- coding: utf-8 -*-

from openerp import models, api, fields, _
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    routing_id = fields.Many2one('mrp.routing', string='Routing')

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None):
        """Add bill of matrials to the configured variant."""
        if custom_values is None:
            custom_values = {}

        variant = super(ProductTemplate, self).create_get_variant(
            value_ids, custom_values=custom_values
        )
        attr_products = variant.attribute_value_ids.mapped('product_id')

        line_vals = [
            (0, 0, {'product_id': product.id}) for product in attr_products
        ]

        values = {
            'product_tmpl_id': self.id,
            'product_id': variant.id,
            'bom_line_ids': line_vals,
            'type': 'normal',
            'routing_id': self.routing_id and self.routing_id.id or False
        }

        self.env['mrp.bom'].create(values)

        return variant


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _get_mako_name(self):
        for product in self:
            try:
                mytemplate = Template(product.mako_tmpl_name or product.display_name)
                buf = StringIO()
                bom = self.env['mrp.bom'].search([('product_id', '=', product.id)], limit=1)
                ctx = Context(buf, product=product,
                              attribute_value=product.attribute_value_ids,
                              steps=product.product_tmpl_id.config_step_line_ids,
                              tempalte=product.product_tmpl_id, bom=bom)
                value = mytemplate.render_context(ctx)
                product.mako_display_name = buf.getvalue().replace('\n', '')
            except Exception as ex:
                _logger.error(_("Error while calculating mako product name: %s")%ex)
                product.mako_display_name = product.display_name
