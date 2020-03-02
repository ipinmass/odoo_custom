
from odoo import api, fields, models

import logging



_logger = logging.getLogger(__name__)

class ExpenseTypeConfig(models.Model):
    _name = 'expense.type.config'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True)
    personal = fields.Boolean('Personal Expense', default=False)
    sequence = fields.Integer(string='Sequence', required=True)