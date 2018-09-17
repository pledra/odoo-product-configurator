from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    # Exclude subconfigurable products from standalone configuration
    product_tmpl_id = fields.Many2one(
        domain=[
            ('config_ok', '=', True),
            ('master_template', '=', True)
        ]
    )
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

    @api.model
    def get_open_step_lines(self, value_ids=None):
        """
        Include config lines with subproducts inside open steps.
        By default they are ignored because they contain no attribute lines.

        :param value_ids: list of value.ids representing the
                          current configuration
        :returns: recordset of accesible configuration steps
        """
        res = super(ProductConfigSession, self).get_open_step_lines(
            value_ids=value_ids
        )
        subproduct_steps = self.product_tmpl_id.config_step_line_ids.filtered(
            lambda x: x.config_subproduct_line_id)
        open_step_lines = res | subproduct_steps
        return open_step_lines.sorted()

    @api.model
    def get_adjacent_steps(self, value_ids=None, active_step_line_id=None):
        """Load steps from subconfigurable products if any"""
        steps = super(ProductConfigSession, self).get_adjacent_steps(
            value_ids=value_ids, active_step_line_id=active_step_line_id
        )
        # At this point the parent method has run and changed the wizard to the
        # next step

        parent_session = self.parent_id

        if not parent_session or not steps:
            return steps

        cfg_step_line_obj = self.env['product.config.step.line']

        # TODO: Move step related methods to sesssion object

        # Todo find a better way to identify the model than through context

        next_step = steps.get('next_step') or cfg_step_line_obj
        prev_step = steps.get('prev_step') or cfg_step_line_obj

        parent_draft_session = parent_session.filtered(
            lambda x: x.state == 'draft'
        )

        # If we have reached the end of a subsession configuration
        if not next_step:
            # Get the first parent / grandparent in draft state
            while parent_draft_session.state != 'draft':
                parent_draft_session = parent_draft_session.parent_id

            # Get all the open steps
            open_steps = parent_draft_session.get_open_step_lines()

            # Get the actual config step corresponding to the id stored
            try:
                step_id = int(parent_draft_session.config_step)
                active_step = open_steps.filtered(lambda l: l.id == step_id)
            except Exception:
                active_step = cfg_step_line_obj

            if active_step:
                index = [l for l in open_steps.sorted()].index(active_step)
                try:
                    steps['next_step'] = open_steps[index + 1]
                except Exception:
                    steps['next_step'] = next_step

        if not prev_step or prev_step == 'select':
            # TODO: Make this step recursive so it checks all the parents
            open_steps = parent_session.get_open_step_lines()
            # TODO: This will fail with more steps that have the same subprod
            subproduct_step = open_steps.filtered(
                lambda l: l.config_subproduct_line_id.subproduct_id == self
            )
            if subproduct_step:
                index = [l for l in open_steps.sorted()].index(subproduct_step)
                try:
                    steps['prev_step'] = open_steps[index - 1]
                except Exception:
                    steps['prev_step'] = prev_step

        return steps


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
                _('Master template cannot assign itself as a subproduct')
            )


class ProductConfigStepLine(models.Model):
    _inherit = 'product.config.step.line'

    @api.multi
    @api.onchange('config_subproduct_line_id')
    def onchange_subproduct_line(self):
        for line in self.filtered(lambda x: x.config_subproduct_line_id):
            line.attribue_line_ids = None

    config_subproduct_line_id = fields.Many2one(
        comodel_name='product.config.subproduct.line',
        help='Subproduct line defined on the template',
        string='Subproduct Line'
    )
