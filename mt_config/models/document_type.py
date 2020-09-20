
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class DocumentTypeConfig(models.Model):
    _name = 'document.type.config'
    _order = 'sequence, id'
    name = fields.Char(string='Name', required=True)
    is_image = fields.Boolean('Is Image?', default=True)
    sequence = fields.Integer(string='Sequence', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Document type already exist !')
    ]
