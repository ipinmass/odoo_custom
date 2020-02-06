
from odoo import api, fields, models

import logging

class TripExpenses(models.Models):
	_name = 'trip.expenses'

	invoice_id = fields.may2one('account.invoice', string='Related Invoice')
	state = fields.selection(related='invoice_id.type', readonly=True)
	