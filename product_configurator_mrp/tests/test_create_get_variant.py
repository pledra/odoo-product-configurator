from odoo.tests.common import TransactionCase
from odoo import SUPERUSER_ID


class CrateGetVariant(TransactionCase):

    def setUp(self):
        super(CrateGetVariant, self).setUp()

        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')
        self.cfg_session = self.env['product.config.session'].create({
            'product_tmpl_id': self.cfg_tmpl.id,
            'user_id': SUPERUSER_ID
        })

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')
        self.attr_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().items()
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

    def test_create_get_variant(self):
        """Test bom creation and update with every new change"""

        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]

        attr_val_ids = self.get_attr_val_ids(conf)

        self.cfg_session.value_ids = attr_val_ids

        variant = self.cfg_session.create_get_variant()

        # self.assertTrue(variant.bom_ids, "No BOM was created with the variant")

        attr_val_engine = self.env.ref(
            'product_configurator.product_attribute_value_228i'
        )

        # Remove the product association so a new bom needs to be generated
        attr_val_engine.product_id = None

        variant = self.cfg_session.create_get_variant()
        import pdb
        pdb.set_trace()

        # Verify new bom has been generated for the respective variant with the
        # lowest sequence
        self.assertTure(len(variant.bom_ids) == 2,
                        "No extra BOM has been generated on "
                        "variant reconfiguration")

        config_bom_lines = self.cfg_session._compute_bom_lines()

        variant_bom = bom = self.env['mrp.bom']._bom_find(
            product=variant, company_id=self.company_id.id
        )

        variant_bom.bom_line_ids

        # Verify the last bom generated has the lowest sequence using _bom_find
        # Also verify the contets between computed bom and current bom match

        # Change products associated with the attribute values in order to
        # change the final computed bom

        # xxx

        # Assert that the new bom is created if materials have changed
