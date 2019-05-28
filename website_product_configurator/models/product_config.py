from odoo import fields, models
from datetime import timedelta


class ProductConfigStepLine(models.Model):
    _inherit = 'product.config.step.line'

    website_tmpl_id = fields.Many2one(
        string='Website Template',
        comodel_name='ir.ui.view',
        domain=lambda s: [(
            'inherit_id', '=', s.env.ref(
                'website_product_configurator.config_form_base').id
        )],
    )

    def get_website_template(self):
        """Return the external id of the qweb template linked to this step"""
        default_view_id = 'website_product_configurator.config_form_radio'
        return self.website_tmpl_id.get_xml_id() or default_view_id


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    def remove_inactive_config_sessions(self):
        check_date = fields.Datetime.from_string(
            fields.Datetime.now()) - timedelta(days=3)
        sessions_to_remove = self.search([
            ('write_date', '<', fields.Datetime.to_string(check_date))
        ])
        if sessions_to_remove:
            sessions_to_remove.unlink()

# [{'name': 'csrf_token', 'value': '94934c5f0fbdfaf8305a579c61d6e48f28bf36ado1559044664'},
# {'name': 'product_tmpl_id', 'value': '39'}, {'name': 'config_session_id', 'value': '322'},
# {'name': '__attribute-6', 'value': '8'},
# {'name': '__attribute-7', 'value': ''},
# {'name': '__attribute-9', 'value': ''},
# {'name': '__attribute-10', 'value': ''},
# {'name': '__attribute-8', 'value': ''},
# {'name': '__attribute-11', 'value': ''},
# {'name': '__attribute-12', 'value': ''}] __attribute-6
# updates  {
#     'value': {'__attribute-6': 8, '__attribute-13': [], 'product_img': None, 'value_ids': [8], 'weight': 210.0, 'price': 25000.0, 'attribute_value_line_ids': []},
#     'domain': {
#         '__attribute-6': [('id', 'in', [8, 9])],
#         '__attribute-7': [('id', 'in', [10, 11, 12, 13, 14])],
#         '__attribute-8': [('id', 'in', [])],
#         '__attribute-9': [('id', 'in', [25, 26, 27])],
#         '__attribute-10': [('id', 'in', [28, 29, 30])],
#         '__attribute-11': [('id', 'in', [31, 32, 33])],
#         '__attribute-12': [('id', 'in', [34, 35])],
#         '__attribute-13': [('id', 'in', [36, 37, 38, 39])]},
#         'open_cfg_step_lines': ['4', '1', '3', '5']}