
from odoo import api, fields, models

import logging


class AccountInvoiec(models.Models):
	_inherit = 'account.invoice'


	member_pay_id = fields.many2one('member.payments', strint='Member Payments')
	payment_proves = fields.binary(string='Payment Prove')
