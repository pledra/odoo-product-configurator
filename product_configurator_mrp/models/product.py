# -*- coding: utf-8 -*-

from openerp import api, fields, models


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'

    quantity = fields.Boolean(
        string='Quantity',
        help='Set quantity for variants related to attribute values selected?'
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing'
    )
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

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None):
        """Add bill of matrials to the configured variant."""
        if custom_values is None:
            custom_values = {}

        session = self.env['product.config.session'].search_session(
                product_tmpl_id=self.id)

        variant = super(ProductTemplate, self).create_get_variant(
            value_ids, custom_values=custom_values)

        qty_attr_lines = self.attribute_line_ids.filtered(lambda l: l.quantity)
        qty_attr_vals = qty_attr_lines.mapped('value_ids')

        attr_products = variant.attribute_value_ids.filtered(
            lambda v: v not in qty_attr_vals).mapped('product_id')

        line_vals = [
            (0, 0, {'product_id': product.id}) for product in attr_products
        ]

        import pdb;pdb.set_trace()

        if session:
            for subsession in session[0].child_ids:
                if subsession.product_tmpl_id.config_ok:
                    # TODO: Create variant and add
                    pass
                else:
                    val_ids = subsession.value_ids.ids
                    domain = [
                        ('product_tmpl_id', '=', subsession.product_tmpl_id.id)
                    ]
                    domain += [
                        ('attribute_value_ids', '=', vid) for vid in val_ids
                    ]
                    product = self.env['product.product'].search(domain)
                    if product:
                        line_vals.append((0, 0, {
                            'product_id': product.id,
                            'product_qty': subsession.quantity
                        }))
                        subsession.action_confirm()
        values = {
            'product_tmpl_id': self.id,
            'product_id': variant.id,
            'bom_line_ids': line_vals,
            'type': 'normal',
            'routing_id': self.routing_id.id or False,
        }

        self.env['mrp.bom'].create(values)

        return variant

    def get_open_step_lines(self, value_ids):
        """Add steps with subproducts regardless of attributes or rules."""
        open_steps = super(ProductTemplate, self).get_open_step_lines(
            value_ids=value_ids
        )
        config_subproduct_lines = self.config_step_line_ids.filtered(
            lambda l: l.config_subproduct_line_id
        )
        open_steps += config_subproduct_lines
        return open_steps.sorted()

    def get_adjacent_steps(self, value_ids, active_step_line_id=None):
        """Load steps from subconfigurable products if any"""
        steps = super(ProductTemplate, self).get_adjacent_steps(
            value_ids=value_ids, active_step_line_id=active_step_line_id
        )
        if not steps:
            return steps

        cfg_step_line_obj = self.env['product.config.step.line']
        cfg_session_obj = self.env['product.config.session']
        cfg_session = cfg_session_obj.create_get_session(self.id)

        if not active_step_line_id:
            # TODO: What if there are no configuration step lines?
            active_line = self.get_open_step_lines(value_ids)[0]
        else:
            active_line = self.config_step_line_ids.filtered(
                lambda l: l.id == active_step_line_id)

        subproduct = active_line.config_subproduct_line_id.subproduct_id.sudo()

        if subproduct.config_ok:
            session = cfg_session_obj.sudo().create_get_session(
                subproduct.id, parent_id=cfg_session.id)
            open_steps = subproduct.get_open_step_lines(
                session[0].value_ids.ids)
            if open_steps:
                steps['active_step'] = open_steps[0]

        next_step = steps.get('next_step') or cfg_step_line_obj
        prev_step = steps.get('prev_step') or cfg_step_line_obj

        # TODO: Take into account subproducts with no configuration steps
        if next_step.config_subproduct_line_id.subproduct_id.config_ok:
            # Retrieve a session (if any) to get the first open step
            session = cfg_session_obj.search_session(
                subproduct.id, parent_id=cfg_session.id)
            # Pass values from found/empty step
            open_steps = subproduct.get_open_step_lines(session.value_ids.ids)
            if open_steps:
                # Override next step with subproduct if open step found
                steps['next_step'] = open_steps[0]

        if prev_step.config_subproduct_line_id.subproduct_id.config_ok:
            session = cfg_session_obj.search_session(
                subproduct.id, parent_id=cfg_session.id)
            open_steps = subproduct.get_open_step_lines(session.value_ids.ids)
            if open_steps:
                steps['prev_step'] = subproduct.get_open_step_lines(
                    session.value_ids.ids)
        return steps
