
from odoo import api, fields, models

import logging



_logger = logging.getLogger(__name__)

class Partner(models.Model):
    
    _inherit = 'res.partner'

    trip_id = fields.Many2one('mt.trip', string='Current Trip')


    @api.model
    def default_get(self,default_fields):
        res = super(Partner, self).default_get(default_fields)

        payable = self.env.ref('mt_trip.default_customer_account_payable').id
        receivable = self.env.ref('mt_trip.default_customer_account_receivable').id
        if payable:
            res['property_account_payable_id'] = payable
        if receivable:
            res['property_account_receivable_id'] = receivable
        return res

    

    