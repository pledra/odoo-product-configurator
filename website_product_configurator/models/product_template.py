from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_float_custom_val(self, custom_value):
        lang = self.env['ir.qweb.field'].user_lang()
        if not custom_value:
            return False
        return custom_value.replace('.', lang.decimal_point)
