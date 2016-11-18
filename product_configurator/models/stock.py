# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_id = fields.Many2one(domain=[('config_ok', '=', False)])
