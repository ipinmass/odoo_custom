
from odoo import api, fields, models

import logging


class AccountInvoiec(models.Models):
	_inherit = 'account.invoice'


	member_id = fields.many2one('trip.member', strint='Member Payments')
	payment_proves = fields.Binary(string='Payment Prove')
