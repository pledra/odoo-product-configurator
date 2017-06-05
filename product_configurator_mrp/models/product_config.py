# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class ProductConfigSubproductLine(models.Model):
    _name = 'product.config.subproduct.line'
    _rec_name = 'subproduct_id'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
    )
    subproduct_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        ondelete='restrict',
        required=True,
        context="{'default_master_template': False, "
                "'default_config_ok': True}",
        help='Subproduct included in master product',
    )
    quantity = fields.Boolean(
        string='Quantity',
        help='Allow setting quantities on this subproduct?'
    )
    multi = fields.Boolean(
        string='Multi',
        help='Allow multiple configurations for this subproduct?'
    )
    required = fields.Boolean(
        string='Required',
        help='Product mandatory for configuring master product',
    )

    @api.constrains('subproduct', 'product_tmpl')
    def _check_subproduct(self):
        self.ensure_one()
        if self.product_tmpl == self.subproduct:
            raise ValidationError(
                _('Master template cannot have assign itself as a subproduct')
            )


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    parent_id = fields.Many2one(
        comodel_name='product.config.session',
        readonly=True,
        ondelete='cascade',
        string='Parent Session'
    )
    child_ids = fields.One2many(
        comodel_name='product.config.session',
        inverse_name='parent_id',
        string='Session Lines',
        help='Child configuration sessions'
    )
    quantity = fields.Integer(
        string='Quantity',
    )

    @api.model
    def get_substeps(self):
        """Retrieve all available substeps from the config session tree"""
        while self.parent_id:
            self = self.parent_id

        cfg_step_lines = self.product_tmpl_id.config_step_line_ids

        config_subproducts = cfg_step_lines.mapped(
            'config_subproduct_line_id.subproduct_id').filtered(
            lambda x: x.config_ok)

        substeps = config_subproducts.mapped('config_step_line_ids').sorted()

        return substeps


class ProductConfigStepLine(models.Model):
    _inherit = 'product.config.step.line'

    config_subproduct_line_id = fields.Many2one(
        comodel_name='product.config.subproduct.line',
        help='Subproduct line defined on the template',
        string='Subproduct Line'
    )
