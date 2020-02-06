
from odoo import api, fields, models

import logging

class Trip(models.Model):
    _name = 'ma.trip'

    state = fields.selection([('open', 'Open'),('progress', 'Progress'),('done', 'Done'), ('cancel', 'Cancel')])
    members = fields.one2many('res.partner', 'trip_id', string='Members')
    expenses = fields.one2many('trip.expenses', 'trip_id', string='Expenses')
   

