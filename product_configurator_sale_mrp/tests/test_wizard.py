from odoo.tests.common import TransactionCase
from odoo import SUPERUSER_ID


class Wizard(TransactionCase):

    def setUp(self):
        super(Wizard, self).setUp()

        self.sale_order_id = self.env.ref('sale.sale_order_3')
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')
        self.cfg_wizard = self.env['product.configurator.sale'].create({
            'product_tmpl_id': self.cfg_tmpl.id,
            'order_id': self.sale_order_id.id,
            'user_id': SUPERUSER_ID
        })

        self.cfg_session = self.cfg_wizard.config_session_id

        self.attr_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.attr_val_ext_ids = {
            v: k for k, v in self.attr_vals.get_external_id().items()
        }

    def get_attr_val_ids(self, ext_ids):
        """Return a list of database ids using the external_ids
        passed via ext_ids argument"""

        value_ids = []

        attr_val_prefix = 'product_configurator.product_attribute_value_%s'

        for ext_id in ext_ids:
            if ext_id in self.attr_val_ext_ids:
                value_ids.append(self.attr_val_ext_ids[ext_id])
            elif attr_val_prefix % ext_id in self.attr_val_ext_ids:
                value_ids.append(
                    self.attr_val_ext_ids[attr_val_prefix % ext_id]
                )

        return value_ids

    def test_wizard_configuration(self):
        """Test whether the sale order line has a bom_id attached to it and the
        MO created from the order uses the bom stored on the order line"""

        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]

        attr_val_ids = set(self.get_attr_val_ids(conf))

        field_prefix = self.cfg_wizard._prefixes['field_prefix']

        while self.cfg_wizard:
            state = self.cfg_wizard.state
            self.cfg_wizard.action_next_step()

            if self.cfg_wizard.state == state:
                break

            step_id = int(self.cfg_wizard.state)

            cfg_step = self.cfg_tmpl.config_step_line_ids.filtered(
                lambda cfg_step: cfg_step.id == step_id
            )

            attr_lines = cfg_step.mapped('attribute_line_ids')

            vals = {}

            for attr_line in attr_lines:
                attr_vals = attr_line.value_ids.filtered(
                    lambda attr_val: attr_val.id in attr_val_ids
                )
                for attr_val in attr_vals:
                    attribute_id = attr_val.attribute_id.id
                    field_name = field_prefix + str(attribute_id)
                    if attr_line.multi:
                        if field_name not in vals:
                            vals[field_name] = [(0, 0, [])]
                        vals[field_name][0][2].append(attr_val.id)
                    else:
                        vals.update({
                            field_name: attr_val.id,
                        })

            self.cfg_wizard.write(vals)

        order_line = self.sale_order_id.order_line.filtered(
            lambda x: x.config_ok
        )
        bom = order_line.bom_id

        self.assertTrue(bom, "Sale order line has no bom linked")

        bom.copy()
        bom.sequence = 10

        self.sale_order_id.action_confirm()

        production_order = order_line.move_ids.created_production_id

        self.assertTrue(production_order,
                        "There was no production order created after sales "
                        "order confirmation")

        self.assertTrue(production_order.bom_id == bom,
                        "Manufacturing order does not use the bom_id stored "
                        "on the sale order line")
