# -*- coding: utf-8 -*-

from odoo import tests


@tests.common.at_install(False)
@tests.common.post_install(True)
class TestUi(tests.HttpCase):

    def setUp(self):
        super(TestUi, self).setUp()
        self.tour = "odoo.__DEBUG__.services['web_tour.tour']"

    def test_admin_configuration(self):
        self.phantom_js(
            "/configurator",
            self.tour + ".run('configure_product', 'test')",
            self.tour + ".tours.configure_product",
            login="admin"
        )

    def test_demo_configuration(self):
        self.phantom_js(
            "/configurator",
            self.tour + ".run('configure_product', 'test')",
            self.tour + ".tours.configure_product",
            login="demo"
        )

    def test_public_configuration(self):
        self.phantom_js(
            "/configurator",
            self.tour + ".run('configure_product', 'test')",
            self.tour + ".tours.configure_product",
        )
