
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date

import logging
_logger = logging.getLogger(__name__)

class Tickets(models.Model):
    _name = 'mt.ticket'

    @api.model
    def _default_currency(self):
        
        return self.env.user.company_id.currency_id

    name = fields.Char('Name', required=True)
    state = fields.Selection([('draft', 'Draft'),('done', 'Done')], default='draft', readonly=True)
    ticket_type = fields.Selection([('hotel', 'Hotel'),('flight', 'Flight')], default='hotel', string='Ticket Type')
    airline_name = fields.Char('Airline Name')
    airline_code = fields.Char('Airline Code')
    e_ticket = fields.Char('E-Ticket Number')
    hotel_name = fields.Char('Hotel Name')
    booking_code = fields.Char('Booking Code')
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', 'True')], required=True)
    sale_price = fields.Monetary('Sale Price', default=0.0)
    purchase_price = fields.Monetary('Purchase Price', default=0.0)
    invoice_id = fields.Many2one('account.invoice', string='Sale Invoice', readonly=True)
    payment_id = fields.Many2one('account.payment', srting='Purchase Payment', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')


    @api.multi
    def _prepare_invoice(self, origin=''):
    
        """
        Prepare the dict of values to create the new invoice for a trip member. 
        """

        self.ensure_one()
        "All transaction will be recorded under the same company since customer company is not important"
        company_id = self.env.user.company_id.id
        journal_id = self.env.ref('mt_trip.mt_journal_customer_payment_id').id

        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        vinvoice = self.env['account.invoice'].new({'partner_id': self.partner_id.id})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals.update({
            'name': 'Invoice - ' + (self.name or ''),
            'origin': origin,
            'type': 'out_invoice',
            'account_id': self.partner_id.property_account_receivable_id.id,
            'journal_id': journal_id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'company_id': company_id,
            'user_id': self.env.user.id
        })
        return invoice_vals

    @api.multi
    def _prepare_invoice_line(self, qty, amt_inv, origin=''):
        self.ensure_one()
        res = {}

        res = {
            'name': self.partner_id.name,
            'origin': origin,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'price_unit': amt_inv,
            'quantity': qty,
            'discount': 0.0,
           
        }
        return res

    @api.one
    def make_sale(self):
        qty = 1

        inv_obj = self.env['account.invoice']
        
        _dp = 1
        
        dp_amt = self.sale_price
        origin = 'Ticket - %s - %s ' %(self.ticket_type, self.partner_id.name)
        inv_vals = self._prepare_invoice(origin=origin)
        inv_created = inv_obj.create(inv_vals)
        inv_line_vals = self._prepare_invoice_line(qty, dp_amt, origin=origin)
        inv_line_vals.update({'invoice_id': inv_created.id})
        self.env['account.invoice.line'].create(inv_line_vals)
        self.invoice_id = inv_created

        if inv_created and self.payment_id:
            self.state = 'done'
        

        return True


    @api.one
    def make_purchase(self):
        partner_id = self.env.ref('mt_ticket.ticket_supplier_generic_ma_travel').id
        if self.purchase_price > 0 and partner_id:
            description = 'Ticket Purchase - ' + self.name
            payment_vals = {
                 'name': 'Payment - %s' %(self.name),
                 'amount': self.purchase_price,
                 'communication': False,
                 'currency_id': self.env.user.company_id.currency_id.id,
                 'description': description,
                 'destination_journal_id': False,
                 'journal_id': self.env.ref('mt_trip.mt_journal_payment_id').id,
                 'message_attachment_count': 0,
                 'partner_bank_account_id': False,
                 'partner_id': partner_id,
                 'partner_type': 'supplier',
                 'payment_date': date.today(),
                 'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                 'payment_type': 'outbound',

            }

            self.payment_id = self.env['account.payment'].create(payment_vals)
            
        if self.payment_id and self.invoice_id:
            self.state = 'done'
        return True