# -*- coding: utf-8 -*-

from openerp import models
from openerp.http import request

from ..wizard.product_configurator import ProductConfigurator as configurator


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def binary_content(
            self, xmlid=None, model='ir.attachment', id=None,
            field='datas', unique=False, filename=None,
            filename_field='datas_fname', download=False,
            mimetype=None,
            default_mimetype='application/octet-stream', env=None):
        env = env or request.env
        # get object and content
        obj = None
        if xmlid:
            obj = env.ref(xmlid, False)
        elif id and model in env.registry:
            obj = env[model].browse(int(id))

        if str(obj._model) == 'product.configurator':
            attachment = obj.custom_value_ids.filtered(
                lambda x: x.attribute_id.id == int(field.split(
                    configurator.custom_field_prefix)[1])
            ).attachment_ids[0]
            id = attachment.id
            model = 'ir.attachment'
            field = 'datas'
        return super(IrHttp, self).binary_content(
            xmlid=xmlid, model=model, id=id, field=field,
            unique=unique, filename=filename, filename_field=filename_field,
            download=download, mimetype=mimetype,
            default_mimetype=default_mimetype, env=env
        )
