
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class TripExpenses(models.Model):
    _name = 'trip.expense'


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char('Name')
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    amount = fields.Monetary(string='Amount', help='Expense Amount', store=True, track_visibility='always')
    expense_type = fields.Many2one('expense.type.config', string='Expense Type', required=True)
    invoice_id = fields.Many2one('account.invoice', string='Supplier Invoice')
    state = fields.Selection(string='State', related='invoice_id.state', readonly=True)
    trip_id = fields.Many2one('mt.trip', string='Related Trip')
    code = fields.Char('Code', help='Can be either Hotel Code or Flight Code, depending on the Expense Type')
    personal = fields.Boolean(string='Is Personal Expense?', related='expense_type.personal')
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer','=', True)])
    passport_no = fields.Char('Passport No', related='partner_id.passport_no')
    passport_img = fields.Binary('Scanned Passport', related='partner_id.passport_img')
    passport_exp = fields.Date('Passport Validity', related='partner_id.passport_exp')
    passport_issued = fields.Date('Passport Issued', related='partner_id.passport_issued')
    dtof_birth = fields.Date('Date of Birth', related='partner_id.dtof_birth')
    trip_id_personal = fields.Many2one('res.partner', string='Customer', domain=[('customer','=', True)])


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



class PersonalTripExpenses(models.Model):
    _name = 'personal.trip.expense'
    _inherit = ['trip.expense']

    trip_id_personal = fields.Many2one('mt.trip')