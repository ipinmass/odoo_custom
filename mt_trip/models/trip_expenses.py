
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

import logging

class TripExpenses(models.Model):
    _name = 'trip.expenses'

    name = fields.Char('Expense Name')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Product Price'))
    invoice_id = fields.Many2one('account.invoice', string='Related Invoice')
    state = fields.Selection(related='invoice_id.type', readonly=True)
    trip_id = fields.Many2one('mt.trip', string='Related Trip')
    paid = fields.Boolean('Paid')
    