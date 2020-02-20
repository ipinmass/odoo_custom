
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class Trip(models.Model):
    _name = 'mt.trip'

    @api.model
    def _default_currency(self):
        
        return self.env.user.company_id.currency_id


    name = fields.Char(string="Name", required=True)
    planned_date = fields.Date(string='Planned Date')
    admin = fields.Many2one('res.partner', string='Admin')
    state = fields.Selection([('open', 'Open'),('progress', 'Progress'),('done', 'Done'), ('cancel', 'Cancel')], default='open')
    member_ids = fields.One2many('trip.member', 'trip_id', string='Members')
    expenses = fields.One2many('account.payment', 'trip_id', string='Expenses')
    trip_template = fields.Many2one('trip.template', 'Trip Template', domain=[('active','=', True)])
    fare = fields.Float('Fare')
    total_expenses = fields.Monetary(string='Total Expenses',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    forcasted_income = fields.Monetary(string='Forcasted Income', help='Computed based on all creaetd invoices including the unpaid one',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    invoice_paid = fields.Monetary(string='Paid Invoices', help='Amount of all paid invoices',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    profit_loss = fields.Monetary(string='Profit/Loss', help='Computed only based on paid invoices (expenses are always considered confirmed)',
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    expense_ids = fields.One2many('trip.expense', 'trip_id', string='Expenses')

    @api.one
    @api.constrains('member_ids')
    def _check_member(self):
        partner_ids = []
        for member in self.member_ids:
            partner_ids.append(member.partner_id.id)
        a = len(partner_ids)
        b = len(set(partner_ids))
        if a != b:
            raise ValidationError(_("Member is already registered in this trip."))


    @api.one
    @api.depends('member_ids.invoice_ids.state', 'member_ids.invoice_ids.amount_total', 'expenses.amount')
    def _compute_amount(self):
        total_expenses = 0.0
        for exp in self.expenses:
            total_expenses += exp.amount
        self.total_expenses = total_expenses
        forcasted_income = 0.0
        invoice_paid = 0.0
        for member in self.member_ids:
            for inv in member.invoice_ids:
                forcasted_income += inv.amount_total
                if inv.state == 'paid':
                    invoice_paid += inv.amount_total
        self.forcasted_income = forcasted_income
        self.invoice_paid = invoice_paid
        self.profit_loss = invoice_paid - total_expenses
        


    @api.multi
    def action_close_registration(self):
        return self.write({'state': 'progress'})

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return  'Trip Member Summary'
   

class TripMember(models.Model):
    _name = 'trip.member'

    # name = fields.Char('Name', related='partner_id.name', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)])
    document_ids = fields.One2many('trip.document', 'member_id', string='Documents')
    dp_amount = fields.Float(string='DP Amount', digits=dp.get_precision('Product Price'))
    invoice_ids = fields.One2many('account.invoice', 'member_id', string='Invoice Lines')
    trip_id = fields.Many2one('mt.trip', string='Trip ID')
    is_document_completed = fields.Boolean('Documents Completed', readonly=True)
    is_invoice_paid = fields.Boolean('Invoices Paid', readonly=True)
    reseller = fields.Many2one('res.partner', string="Reseller", domain=[('customer', '=', False)])
    reseller_fee = fields.Float(string='Reseller Fee', digits=dp.get_precision('Product Price'))
    discount = fields.Float('Discount (%)')
    installment_times = fields.Integer('Installment Times', required=True, default=1)
    payment_type = fields.Selection([('full', 'Full'), ('credit', 'Credit')], string='Payment Type', default='full')
    is_reseller_paid = fields.Boolean('Reseller Paid', readonly=True, default=False)
    visa_appointment_date = fields.Date('VISA Appointment Date')
    hotel_code = fields.Char('Hotel Code')
    flight_code = fields.Char('Flight Code')
    
    @api.one
    @api.constrains('discount')
    def _check_discount(self):
        if self.discount > 100:
            raise ValidationError(_("Discount cannot exceed 100%!."))

    

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
            'name': 'Invoice - ' + (self.trip_id and self.trip_id.name or ''),
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
            'discount': self.discount,
           
        }
        return res

    @api.one
    def action_invoice_create(self):
        qty = 1
        discount = self.discount or 0.0
        inv_obj = self.env['account.invoice']
        
        _dp = 1
        
        # handle the down payment part
        dp_amt = self.dp_amount
        if dp_amt > 0.0:
            origin = 'DP - %s - %s ' %(self.partner_id.name, self.trip_id.name)
            inv_vals = self._prepare_invoice(origin=origin)
            inv_vals.update({'name': 'DP - ' + self.trip_id.name})
            inv_created = inv_obj.create(inv_vals)
            inv_line_vals = self._prepare_invoice_line(qty, dp_amt, origin=origin)
            # omit discount from down payment invoice
            inv_line_vals['discount'] = 0.0
            inv_line_vals.update({'invoice_id': inv_created.id})
            self.env['account.invoice.line'].create(inv_line_vals)
            inv_created.update({'member_id': self.id})
        # make the invoice paid
        # inv_created.action_invoice_open()
        origin = 'INV - %s - %s ' %(self.partner_id.name, self.trip_id.name)
        amt_inv = round((self.trip_id.fare-self.dp_amount)/self.installment_times, _dp)
        for item in range(1, self.installment_times + 1):
            origin = 'INV - %s - %s - %s ' %(item, self.partner_id.name, self.trip_id.name)
            inv_vals = self._prepare_invoice(origin=origin)
            inv_vals['origin'] = inv_vals['origin'] + ' - ' + str(item)
            inv_created = inv_obj.create(inv_vals)
            inv_line_vals = self._prepare_invoice_line(qty, amt_inv, origin=origin)
            inv_line_vals.update({'invoice_id': inv_created.id})
            self.env['account.invoice.line'].create(inv_line_vals)
            inv_created.update({'member_id': self.id})

        return True


    @api.multi
    def action_invoice_show(self):
        invoices = self.invoice_ids
        action_vals = {
            'name': _('Invoices'),
            'domain': [('id', 'in', invoices.ids)],
            'view_type': 'form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        if len(invoices) == 1:
            action_vals.update({'res_id': invoices[0].id, 'view_mode': 'form'})
        else:
            action_vals['view_mode'] = 'tree,form'
        action_vals['views'] = [(self.env.ref('account.invoice_tree').id, 'tree'), (self.env.ref('account.invoice_form').id, 'form')]
        return action_vals

    # @api.one
    # def action_pay_reseller(self):
    #     amt = self.reseller_fee
    #     acp = self.env['account.payment']
    #     if amt > 0.0:
    #         partner = self.reseller_id




    @api.one
    def action_documents_create(self):
        templates = self.trip_id and self.trip_id.trip_template
        trip_doc_obj = self.env['trip.document']
        if templates:
            for doc in templates.documents:
                v = {
                    'name': doc.name,
                    'member_id': self.id
                }
                trip_doc_obj.create(v)
        return True

    @api.one
    def action_pay_reseller(self):
        if not self.reseller or self.reseller_fee <= 0.0:
            return True
        expense_obj = self.env['trip.expense']
        expense_vals = {
            'name': 'Reseller Payment - %s - %s ' %(self.reseller.name, self.trip_id.name),
            'amount': self.reseller_fee,
            'expense_type': 'other',
            'trip_id': self.trip_id.id
        }
        return True


    @api.one
    def action_documents_show(self):
        return

    

class TripTemplate(models.Model):
    _name = 'trip.template'


    name = fields.Char('Destination')
    documents = fields.One2many('trip.document.template', 'template_id', string='Documents')
    active = fields.Boolean('Active', default=True)


class TripDocumentTemplate(models.Model):
    _name = 'trip.document.template'

    template_id = fields.Many2one('trip.template', string='Trip Template')
    name = fields.Char('Document Name')
    

class TripDocument(models.Model):
    _name = 'trip.document'

    member_id = fields.Many2one('trip.member', string='Trip Template')
    name = fields.Char('Document Name')
    is_image = fields.Boolean('Scanned Image?', readonly=True)
    attachment = fields.Binary('Attachment')
