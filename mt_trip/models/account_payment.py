
from odoo import api, fields, models

import logging


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    member_id = fields.Many2one('trip.member', strint='Member Payments')
    payment_proves = fields.Binary(string='Payment Prove')
