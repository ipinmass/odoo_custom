
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    member_id = fields.Many2one('trip.member', strint='Member Payments')
    payment_prove = fields.Binary(string='Payment Prove')
    payment_prove_img = fields.Binary(string='Scanned Payment Prove')
    is_image = fields.Boolean('Picture ?', default=True, required=True)
