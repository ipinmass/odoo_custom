
from odoo import api, fields, models

import logging


class MemberPayments(models.Model):
    _name = 'member.payments'

    state = fields.Selection([('unpaid', 'Unpaid'),('progress', 'Progress'),('paid', 'Paid')])
    payment_type = fields.Selection([('full', 'Full Payment'), ('partial', 'Partial (credit)')])
    invoice_ids = fields.One2many('account.invoice', 'member_pay_id', string='Member Trip Payment')
    member_id = fields.Many2one('res.partner', string='Member Name')
    down_payment = fields.Float(string='Downn Payment')

