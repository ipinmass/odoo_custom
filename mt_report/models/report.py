# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from itertools import groupby

import logging
_logger = logging.getLogger(__name__)


class Report(models.TransientModel):
    _name = 'mt.reporting'

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    income = fields.Monetary(string='In-Payment Amount', readonly=True)
    outcome = fields.Monetary(string='Out-Payment Amount', readonly=True)
    balance = fields.Monetary(sting='Balance', readonly=True)
    total_tax = fields.Monetary('Total Tax Expenses', readonly=True, help='Counted from all Expenses with type Tax')
    dt_from = fields.Date(string='Date From')
    dt_to = fields.Date(string='Date To')
    show_report = fields.Boolean('Refresh Report', default=False)

    @api.one
    def action_show_report(self):
        return True

    @api.onchange('show_report')
    def _onchange_show_report(self):
        _sql = '''
            WITH
                acc_in AS (SELECT id AS id from account_account WHERE code = 'CR01'),
                acc_out AS (SELECT id AS id from account_account WHERE code = 'CP01'),

                incoming AS (
                SELECT 1 as col1, aml.account_id, sum(aml.credit) AS cr
                FROM account_move_line aml
                JOIN acc_in ON acc_in.id=aml.account_id
                JOIN account_move am ON aml.move_id=am.id AND am.state = 'posted'

                GROUP BY account_id, col1

                ),

                outcoming AS (
                SELECT 1 as col1, aml.account_id, sum(aml.debit) AS dr
                FROM account_move_line aml
                JOIN acc_out ON acc_out.id=aml.account_id
                JOIN account_move am ON aml.move_id = am.id AND am.state = 'posted'

                GROUP BY account_id,col1

                )
                SELECT incoming.cr AS income, outcoming.dr AS outcome, (incoming.cr - outcoming.dr) AS balance FROM incoming FULL JOIN outcoming ON incoming.col1=outcoming.col1
        '''
        self.env.cr.execute(_sql)
        res = self.env.cr.dictfetchall()
        balance = res and res[0].get('balance', 0.0) or 0.0
        income = res and res[0].get('income', 0.0) or 0.0
        outcome = res and res[0].get('outcome', 0.0) or 0.0
        self.income = income
        self.outcome = outcome
        _sql_tax = _sql.replace('CR01', 'TR01').replace('CP01', 'TP01')
        self.env.cr.execute(_sql_tax)
        res = self.env.cr.dictfetchall()
        total_tax = res and res[0].get('outcome', 0.0) or 0.0
        self.total_tax = total_tax
        self.balance = balance - total_tax
