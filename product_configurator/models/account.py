# -*- coding: utf-8 -*-

from openerp import models, fields


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    product_id = fields.Many2one(domain=[('config_ok', '=', False)])
