
from odoo import api, fields, models

import logging



_logger = logging.getLogger(__name__)

class Partner(models.Model):
    
    _inherit = 'res.partner'

    trip_id = fields.may2one('mt.trip', string='Current Trip')
    