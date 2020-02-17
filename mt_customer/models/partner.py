
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
    

