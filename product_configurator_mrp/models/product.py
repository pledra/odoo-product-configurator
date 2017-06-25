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
            bom = bom_obj.browse(bom_obj._bom_find(product_id=variant.id))
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
                product_tmpl_id=self.id)

        self = self.with_context(config_session_id=session.id)

        variant = super(ProductTemplate, self).create_get_variant(
            value_ids, custom_values=custom_values)

        bom_obj = self.env['mrp.bom']

        bom = bom_obj.browse(bom_obj._bom_find(product_id=variant.id))

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
        # At this point the parent method has run and changed the wizard to the
        # next step
        if not steps:
            return steps

        cfg_step_line_obj = self.env['product.config.step.line']

        # TODO: Move step related methods to sesssion object

        # Todo find a better way to identify the model than through context
        wiz_model = self._context.get('wizard_model', 'product.configurator')
        wiz = self.env[wiz_model].browse(self._context.get('wizard_id'))

        next_step = steps.get('next_step') or cfg_step_line_obj
        prev_step = steps.get('prev_step') or cfg_step_line_obj

        parent_session = wiz.config_session_id.parent_id
        parent_draft_session = parent_session
        parent_draft_session_tmpl = parent_draft_session.product_tmpl_id

        # If we have reached the end of a subsession configuration
        if not next_step and parent_session:

            # Get the first grandparent in draft state
            while parent_draft_session.state != 'draft':
                parent_draft_session = parent_draft_session.parent_id

            # Get all the open steps
            open_steps = parent_draft_session_tmpl.get_open_step_lines(
                parent_draft_session.value_ids.ids
            )

            # Get the actual config step corresponding to the id stored
            try:
                step_id = int(parent_draft_session.config_step)
                active_step = open_steps.filtered(lambda l: l.id == step_id)
            except:
                active_step = cfg_step_line_obj

            if active_step:
                index = [l for l in open_steps.sorted()].index(active_step)
                try:
                    steps['next_step'] = open_steps[index + 1]
                except:
                    steps['next_step'] = next_step

        if not prev_step or prev_step == 'select' and parent_session:
            # TODO: Make this step recursive so it checks all the parents
            open_steps = parent_session.product_tmpl_id.get_open_step_lines(
                parent_session.value_ids.ids
            )
            # TODO: This will fail with more steps that have the same subprod
            subproduct_step = open_steps.filtered(
                lambda l: l.config_subproduct_line_id.subproduct_id == self
            )
            if subproduct_step:
                index = [l for l in open_steps.sorted()].index(subproduct_step)
                try:
                    steps['prev_step'] = open_steps[index - 1]
                except:
                    steps['prev_step'] = prev_step

        return steps
