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
    payment_type = fields.Selection([('full', 'Full'),('credit', 'Credit')], default='full')
    # installment_times = fields.Integer('Installment Times', default=1)
    expense_ids = fields.One2many('trip.expense', 'ticket_id', string='Expenses')
    invoice_ids = fields.One2many('account.invoice', 'ticket_id', string='Sale Invoice')
    sale_price = fields.Monetary('Sale Price', default=0.0)
    purchase_price = fields.Monetary('Purchase Price', default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    is_purchased = fields.Boolean('Is Purchased', default=False)
    is_invoice_created = fields.Boolean('Invoice Crated', default=False)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
        readonly=True, states={'draft': [('readonly', False)]}, help="Date Due is calculated based on selected Payment Term.\
                                                                      Keeping this value empty means a direct payment.")


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
        if self.payment_type == 'credit':
            line_no = 1
            computed = self.payment_term_id.compute(self.sale_price)[0]
            for (date, amt) in computed:

            # for t in range(0, self.installment_times):
            #     amt = self.sale_price/self.installment_times
                origin = 'Ticket - %s - %s ' %(self.ticket_type, self.partner_id.name)
                inv_vals = self._prepare_invoice(origin=origin)
                
                inv_vals.update({
                    'name': 'Invoice - %s - %s' % (str(line_no+1), self.name),
                    'ticket_id': self.id,
                    'date_invoice': fields.Date.today(),
                    'payment_term_id': self.payment_term_id and self.payment_term_id.id or False,
                    'date_due': date,
                    })
                _logger.info('date, amt======== %s', ( computed))
                inv_created = inv_obj.create(inv_vals)
                inv_line_vals = self._prepare_invoice_line(qty, amt, origin=origin)
                inv_line_vals.update({'invoice_id': inv_created.id})
                self.env['account.invoice.line'].create(inv_line_vals)
                inv_line_vals = self._prepare_invoice_line(qty, amt, origin=origin)
                line_no +=1
        else:
            amt = self.sale_price
            origin = 'Ticket - %s - %s ' %(self.ticket_type, self.partner_id.name)
            inv_vals = self._prepare_invoice(origin=origin)
            inv_vals.update({
                    'name': 'Invoice - %s' % (self.name),
                    'ticket_id': self.id,
                    'date_invoice': fields.Date.today(),
                    'payment_term_id': self.payment_term_id and self.payment_term_id.id or False,
                    'date_due': fields.Date.today()
                    })
            inv_created = inv_obj.create(inv_vals)
            inv_line_vals = self._prepare_invoice_line(qty, amt, origin=origin)
            inv_line_vals.update({'invoice_id': inv_created.id})
            self.env['account.invoice.line'].create(inv_line_vals)
            
        self.is_invoice_created = True
        return True


    @api.one
    def make_purchase(self):
        partner_id = self.env.ref('mt_ticket.ticket_supplier_generic_ma_travel').id
        
        expense_obj = self.env['trip.expense']
        expense_vals = {
            'name': 'Ticket Purchasing - %s ' %(self.name),
            'amount': self.purchase_price,
            'expense_type': self.env['expense.type.config'].search([('name','ilike', self.ticket_type)]).id,
            'ticket_id': self.id
        }
        _logger.info('expense_vals============ %s', expense_vals)
        created_expense = expense_obj.create(expense_vals)
        created_expense.button_confirm()
        self.is_purchased = True

        return True

    @api.one
    def make_done(self):
        if self.is_purchased and self.is_invoice_created:
            if not all ([inv.state == 'paid' for inv in self.invoice_ids]):
                raise UserError(_('This ticket still has unpaid Invoice(s). Make sure to mark all Invoices as paid!'))
            if not all ([exp.state == 'paid' for exp in self.expense_ids]):
                raise UserError(_('This ticket still has unpaid Expense(s). Make sure to mark all Expenses as paid!'))
        self.state = 'done'
            