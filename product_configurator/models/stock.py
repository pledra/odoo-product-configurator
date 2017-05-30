# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one(domain=['|', ('reuse_variant', '=', True), ('config_ok', '=', False)])
