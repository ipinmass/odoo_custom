
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class DocumentTypeConfig(models.Model):
    _inherit = 'res.company'

    watermark_img = fields.Binary('Watermark Image')