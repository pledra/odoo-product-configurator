from openerp import api, fields, models
from openerp.http import request


class ProductConfigStep(models.Model):
    _inherit = 'product.config.step'

    """Extend the configuration step with a selectable view that will
    display the content in the frontend for each separate step"""

    view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Website View',
        domain=lambda s: [(
            'inherit_id', '=', s.env.ref(
                'website_product_configurator.config_form_base').id
        )],
        help="Specific view for rendering this attribute in the frontend"
    )


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    """Set SID for public user. There is no other way to distinguish between
    users that are not logged in with a personal username"""

    session_id = fields.Char(
        string='Session ID',
        help='Website session ID to identify user'
    )
    website = fields.Boolean(
        string='Website',
        help='Used to filter website configuration session from others'
    )

    @api.multi
    def get_session_search_domain(self, product_tmpl_id, state='draft',
                                  parent_id=None):
        """Add website relevant arguments to the standard search domain"""
        res = super(ProductConfigSession, self).get_session_search_domain(
            product_tmpl_id=product_tmpl_id, state=state,
            parent_id=parent_id
        )
        # TODO maybe have link with website instead of boolean?
        if 'website_id' in self._context:
            public_user_id = request.env.ref('base.public_user').id
            res.append(('website', '=', True))
            if request.env.uid == public_user_id:
                res.append(('session_id', '=', request.session.sid))
        return res

    @api.multi
    def get_session_vals(self, product_tmpl_id, parent_id=None):
        """Add website relevant arguments to the session create values"""
        res = super(ProductConfigSession, self).get_session_vals(
            product_tmpl_id=product_tmpl_id, parent_id=parent_id
        )
        if 'website_id' in self._context:
            res.update(website=True)
            public_user_id = request.env.ref('base.public_user').id
            if request.env.uid == public_user_id:
                res.update(session_id=request.session.sid)
        return res
