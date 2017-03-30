# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    product_id = fields.Many2one(domain=[('config_ok', '=', False)])
