from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class ProductConfig(TransactionCase):

	def setUp(self):
		super(ProductConfig, self).setUp()
		self.config_product_1 = self.env.ref('product_configurator.product_config_line_gasoline_engines')

	# TODO :: Left
	def test_00_check_value_attributes(self):
		self.config_product_1.attribute_line_id = 6
		self.config_product_1.attribute_line_id.attribute_id = 9