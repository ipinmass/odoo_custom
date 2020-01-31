
from odoo import api, fields, models

import logging



_logger = logging.getLogger(__name__)

class Partner(models.Model):
    
    _inherit = 'res.partner'

    passport_img = fields.Binary("Scanned Passport", attachment=True,
        help="This field holds the scanned passport",)
    

    @api.model
    def default_get(self,default_fields):
    	res = super(Partner, self).default_get(default_fields)

    	record_id = self.env.ref('customer_mt.default_customer_account_payable').id
    	
    	if record_id:
    		res['property_account_payable_id'] = record_id
    	return res

    
