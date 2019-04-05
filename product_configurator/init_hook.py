import logging

logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Transfer existing weight values to weight_dummy after installation
    since now the weight field is computed
    """
    cr.execute("UPDATE product_product SET weight_dummy = weight")
