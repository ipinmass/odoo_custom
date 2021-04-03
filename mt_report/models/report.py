# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from itertools import groupby
import calendar
import logging
_logger = logging.getLogger(__name__)

MONTH_LIST = [(1, 'January'),
              (2, 'February'),
              (3, 'March'),
              (4, 'April'),
              (5, 'May'),
              (6, 'June'),
              (7, 'July'),
              (8, 'August'),
              (9, 'September'),
              (10, 'October'),
              (11, 'November'),
              (12, 'December')]

class Report(models.Model):
    _name = 'mt.reporting'

    name = fields.Char('Name', compute='assign_name')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    income = fields.Monetary(string='In-Payment Amount', readonly=True, compute='_compute_balance')
    outcome = fields.Monetary(string='Out-Payment Amount', readonly=True, compute='_compute_balance')
    balance = fields.Monetary(sting='Balance', readonly=True, compute='_compute_balance')
    total_tax = fields.Monetary('Total Tax Expenses', readonly=True, help='Counted from all Expenses with type Tax')
    year =  fields.Char('Year Period', required=True)
    report_item = fields.One2many('mt.reporting.item', 'reporting_id', string='Monthly Details')
    @api.one
    def assign_name(self):
        self.name = self.year

    @api.one
    def _compute_balance(self):
        income = 0
        outcome = 0
        total_tax = 0
        balance = 0
        for item in self.report_item:
            income += item.income
            outcome += item.outcome
            total_tax += item.total_tax
            balance += item.balance
        self.income = income
        self.outcome = outcome
        self.total_tax = total_tax
        self.balance = balance

    @api.one
    def initiate(self):
        DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
        if self.year:
            year = int(self.year)
            for idx, m in MONTH_LIST:
                dt_from_str = '%s-%s-01' %(year, idx)
                dt_to_str = '%s-%s-%s' %(year, idx, calendar.monthrange(year, idx)[1])
                v = {
                    'month': idx,
                    'reporting_id': self.id,
                    'dt_from': dt_from_str,
                    'dt_to':dt_to_str
                }
                print('vals========= %s', v)
                self.env['mt.reporting.item'].create(v)


class ReportItem(models.Model):
    _name = 'mt.reporting.item'

    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    reporting_id = fields.Many2one('mt.reporting', string='Reporting ID')
    income = fields.Monetary(string='In-Payment Amount', compute='_compute_balance', readonly=True)
    outcome = fields.Monetary(string='Out-Payment Amount', compute='_compute_balance', readonly=True)
    balance = fields.Monetary(sting='Balance', compute='_compute_balance', readonly=True)
    total_tax = fields.Monetary('Total Tax Expenses', readonly=True, help='Counted from all Expenses with type Tax')
    dt_from = fields.Date('Date From')
    dt_to = fields.Date(('Date To'))
    month = fields.Selection([(1, 'January'),
                              (2, 'February'),
                              (3, 'March'),
                              (4, 'April'),
                              (5, 'May'),
                              (6, 'June'),
                              (7, 'July'),
                              (8, 'August'),
                              (9, 'September'),
                              (10, 'October'),
                              (11, 'November'),
                              (12, 'December')], string='Month')

    @api.one
    def _compute_balance(self):
        _sql = '''
            WITH
                acc_in AS (SELECT id AS id from account_account WHERE code = 'CR01'),
                acc_out AS (SELECT id AS id from account_account WHERE code = 'CP01'),

                incoming AS (
                SELECT 1 as col1, aml.account_id, sum(aml.credit) AS cr
                FROM account_move_line aml
                JOIN acc_in ON acc_in.id=aml.account_id
                JOIN account_move am ON aml.move_id=am.id AND am.state = 'posted'
                WHERE am.date BETWEEN '%s' AND '%s'

                GROUP BY account_id, col1

                ),

                outcoming AS (
                SELECT 1 as col1, aml.account_id, sum(aml.debit) AS dr
                FROM account_move_line aml
                JOIN acc_out ON acc_out.id=aml.account_id
                JOIN account_move am ON aml.move_id = am.id AND am.state = 'posted'
                WHERE am.date BETWEEN '%s' AND '%s'

                GROUP BY account_id,col1

                )
                SELECT incoming.cr AS income, outcoming.dr AS outcome, (incoming.cr - outcoming.dr) AS balance FROM incoming FULL JOIN outcoming ON incoming.col1=outcoming.col1
        ''' %(self.dt_from, self.dt_to, self.dt_from, self.dt_to)
        self.env.cr.execute(_sql)
        res = self.env.cr.dictfetchall()
        balance = res and res[0].get('balance', 0.0) or 0.0
        self.income = res and res[0].get('income', 0.0) or 0.0
        self.outcome = res and res[0].get('outcome', 0.0) or 0.0
        _sql_tax = _sql.replace('CR01', 'TR01').replace('CP01', 'TP01')
        self.env.cr.execute(_sql_tax)
        res = self.env.cr.dictfetchall()
        total_tax = res and res[0].get('outcome', 0.0) or 0.0
        self.total_tax = total_tax
        self.balance = balance - total_tax