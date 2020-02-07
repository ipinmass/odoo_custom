
from odoo import api, fields, models

import logging



_logger = logging.getLogger(__name__)

class Partner(models.Model):
    
    _inherit = 'res.partner'

    passport_img = fields.Binary("Scanned Passport", attachment=True,
        help="This field holds the scanned passport",)
    gender = fields.Selection([('male', 'Male'),('female', 'Female')], string="Gender", default='male', required=True)
    dtof_birth = fields.Date(string='Date of Birth')
    passport_no = fields.Char(string='Passport Number')
    passport_exp = fields.Date(string='Passport Validity')
    

    @api.model
    def default_get(self,default_fields):
        res = super(Partner, self).default_get(default_fields)

        payable = self.env.ref('mt_customer.default_customer_account_payable').id
        receivable = self.env.ref('mt_customer.default_customer_account_receivable').id
        if payable:
            res['property_account_payable_id'] = payable
        if receivable:
            res['property_account_receivable_id'] = receivable
        return res

    
