
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    trip_id = fields.Many2one('mt.trip', string='Related Trip')
    description = fields.Char('Description', required=True)
    reseller_payment = fields.Boolean('Reseller Fee Pyament ?', default=False)


    @api.model
    def default_get(self, default_fields):
        res = super(AccountPayment, self).default_get(default_fields)
        c_journal_id = self.env.ref('mt_trip.mt_journal_customer_payment_id').id

        if self._context and self._context.get('trip_context') and self._context.get('trip_context') == 'trip_payment':
            res['payment_type'] = 'outbound'
        res['journal_id'] = c_journal_id
        return res

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(AccountPayment, self)._onchange_journal()
        return res

    @api.onchange('reseller_payment')
    def _reseller_payment(self):
        

        a = self.with_context(prefetch_fields=False).trip_id.id
        a = dir(a)
        # _logger.info('============== _context %s', dir(self.with_context(prefetch_fields=False)))
        _logger.info('============== _context %s', a)
        return {}


class TripExpenses(models.Model):
    _name = 'trip.expense'


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char('Name')
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    amount = fields.Monetary(string='Amount', help='Amount of all paid invoices', store=True, track_visibility='always')
    expense_type = fields.Selection([('hotel', 'Hotel'),('flight', 'Flight'),('other', 'Other')], string='Expense Type', default='hotel', required=True)
    invoice_id = fields.Many2one('account.invoice', string='Supplier Invoice')
    ticket_code = fields.Char('Code')
    state = fields.Selection(string='State', related='invoice_id.state', readonly=True)
    trip_id = fields.Many2one('mt.trip', string='Related Trip')
    people = fields.Integer('Number of People')

    @api.one
    def button_confirm(self):
        inv_obj = self.env['account.invoice']
        partner_id = self.env.ref('mt_trip.supplier_generic_ma_travel')
        journal_id = self.env.ref('mt_trip.mt_journal_payment_id').id
        company_id = self.env.user.company_id

        if not all ([partner_id, journal_id]):
            return True

        vinvoice = self.env['account.invoice'].new({'partner_id': partner_id.id})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals = {
            'name': 'Sup Invoice - ' + (self.trip_id and self.trip_id.name or ''),
            'origin': self.name or '',
            'type': 'in_invoice',
            'account_id': partner_id.property_account_payable_id.id,
            'journal_id': journal_id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'company_id': company_id.id,
            'user_id': self.env.user.id,
            'partner_id': partner_id.id
        }

        invoice_line_vals = {
            'name': partner_id.name,
            'origin': self.name or '',
            'account_id': partner_id.property_account_payable_id.id,
            'price_unit': self.amount,
            'quantity': 1,
            'discount': 0.0,
           
        }
        inv_created = inv_obj.create(invoice_vals)
        
        invoice_line_vals.update({'invoice_id': inv_created.id})
        self.env['account.invoice.line'].create(invoice_line_vals)
        self.invoice_id =  inv_created
        inv_created.action_invoice_open()
        return True


    @api.one
    def assign_hotel(self):
        if self.expense_type == 'hotel':
            members_to_code = self.trip_id.member_ids.filtered(lambda member: member.hotel_code == '' or member.hotel_code == False)
            dif =  self.people - len(members_to_code)
            if dif <= 0:
                for d in range(0, self.people):
                    members_to_code[d].hotel_code = self.ticket_code
                    self.people = 0
            else:
                for m in members_to_code:
                    m.hotel_code = self.ticket_code
                self.people = dif
        return True





