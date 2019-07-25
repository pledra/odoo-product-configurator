import odoo.tests


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_01_admin_config_tour(self):
        self.phantom_js(
            "/", "odoo.__DEBUG__.services['web_tour.tour'].run('config')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.config.ready",
            login="admin"
        )

    def test_02_demo_config_tour(self):
        self.phantom_js(
            "/", "odoo.__DEBUG__.services['web_tour.tour'].run('config')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.config.ready",
            login="demo"
        )
