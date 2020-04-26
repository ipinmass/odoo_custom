
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date

import logging
_logger = logging.getLogger(__name__)


class Trip(models.Model):
    _name = 'mt.trip'
    _order = 'planned_date, id'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    name = fields.Char(string="Name", required=True, )
    planned_date = fields.Date(string='Planned Date',)
    admin = fields.Many2one('res.partner', string='Admin', domain=[('customer', '=', False)], readonly=True, )
    state = fields.Selection([('open', 'Open'), ('progress', 'Progress'), ('done', 'Done'), ('cancel', 'Cancel')],
                             default='open', index=True, track_visibility='onchange', copy=False)
    member_ids = fields.One2many('trip.member', 'trip_id', string='Members',)
    trip_template = fields.Many2one('trip.template', 'Trip Template', domain=[('active', '=', True)])
    fare = fields.Float('Fare')
    total_expenses = fields.Monetary(string='Total Expenses', store=True, readonly=True,
                                     compute='_compute_amount', track_visibility='always')
    forcasted_income = fields.Monetary(string='Forcasted Income', help='Computed based on all creaetd invoices including the unpaid one',
                                       store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    invoice_paid = fields.Monetary(string='Paid Invoices', help='Amount of all paid invoices',
                                   store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    profit_loss = fields.Monetary(string='Profit/Loss', help='Computed only based on paid invoices (expenses are always considered confirmed)',
                                  store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=_default_currency, track_visibility='always')
    expense_ids = fields.One2many('trip.expense', 'trip_id', string='Expenses')
    personal_expenses = fields.One2many('trip.expense', 'trip_id_personal', string='Expenses')

    @api.one
    @api.constrains('member_ids')
    def _check_member(self):
        passports = {}
        for member in self.member_ids:
            passport = member.partner_id.passport_no or ''
            if passport and passport not in passports:
                passports.update({passport: member.partner_id.name})
            elif passport and passport in passports:
                raise ValidationError(_("The member is already registered with passport: %s. Existed: %s. Attempting to add: %s"
                                      % (passport, passports.get(passport), member.partner_id.name)))
            else:
                raise ValidationError(_("This member has no passport data. Name: %s" % member.partner_id.name))

    @api.one
    @api.depends('member_ids.invoice_ids.state', 'member_ids.invoice_ids.amount_total', 'expense_ids.amount')
    def _compute_amount(self):
        total_expenses = 0.0
        for exp in self.expense_ids:
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
        self.state = 'progress'
        return True

    @api.multi
    def make_done(self):
        self.state = 'done'
        return True

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Trip Member Summary'

    @api.multi
    def _get_report_base_filename_2(self):
        self.ensure_one()
        return 'Payment Summary'


class TripMember(models.Model):
    _name = 'trip.member'
    _order = 'sequence, id'

    # name = fields.Char('Name', related='partner_id.name', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)], required=True)
    document_ids = fields.One2many('trip.document', 'member_id', string='Documents')
    dp_amount = fields.Float(string='DP Amount', digits=dp.get_precision('Product Price'))
    invoice_ids = fields.One2many('account.invoice', 'member_id', string='Invoice Lines')
    trip_id = fields.Many2one('mt.trip', string='Trip ID')
    is_document_completed = fields.Boolean('Documents Completed', readonly=True)
    is_invoice_paid = fields.Boolean('Invoices Paid', readonly=True)
    reseller = fields.Many2one('res.partner', related='partner_id.reseller_id', string="Reseller", domain=[('customer', '=', False)])
    reseller_fee = fields.Float(string='Reseller Fee', digits=dp.get_precision('Product Price'))
    discount = fields.Float('Discount (%)')
    installment_times = fields.Integer('Installment Times', required=True, default=1)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
                                      help="Date Due is calculated based on selected Payment Term.\
                              Keeping this value empty means a direct payment. Assign multiple\
                              lines of payment terms on the Payment Terms configuration to \
                              issue multiple invoices")

    payment_type = fields.Selection([('full', 'Full'), ('credit', 'Credit')], string='Payment Type', default='full')
    is_reseller_paid = fields.Boolean('Reseller Paid', readonly=True, default=False)
    visa_appointment_date = fields.Date('VISA Appointment Date')
    hotel_code = fields.Char('Hotel Code')
    flight_code = fields.Char('Flight Code')
    dp_proof = fields.Binary('DP proof')
    sequence = fields.Integer('No.')
    show_pay_reseller = fields.Boolean('Show Pay Reseller', default=False, compute='_check_show_reseller')

    @api.one
    @api.depends('is_reseller_paid', 'invoice_ids', 'invoice_ids.state')
    def _check_show_reseller(self):
        inv_paid = self.invoice_ids and all([inv.state == 'paid' for inv in self.invoice_ids])
        if inv_paid and not self.is_reseller_paid:
            self.show_pay_reseller = True

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
            'user_id': self.env.user.id,
            'date_invoice': fields.Date.today(),
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
            if not self.dp_proof:
                raise ValidationError(_("Down Payment proof is required"))
            origin = 'DP - %s - %s ' % (self.partner_id.name, self.trip_id.name)
            inv_vals = self._prepare_invoice(origin=origin)
            inv_vals.update({'name': 'DP - ' + self.trip_id.name})
            inv_vals.update({'payment_prove_img': self.dp_proof})
            inv_created = inv_obj.create(inv_vals)
            inv_line_vals = self._prepare_invoice_line(qty, dp_amt, origin=origin)
            # omit discount from down payment invoice
            inv_line_vals['discount'] = 0.0
            inv_line_vals.update({'invoice_id': inv_created.id})
            self.env['account.invoice.line'].create(inv_line_vals)
            inv_created.update({'member_id': self.id})

        if self.payment_term_id and self.payment_type == 'credit':
            line_no = 1
            for _date, amt in self.payment_term_id.compute(self.trip_id.fare - self.dp_amount)[0]:
                origin = 'INV - %s - %s - %s ' % (str(line_no), self.partner_id.name, self.trip_id.name)
                inv_vals = self._prepare_invoice(origin=origin)
                inv_vals.update({'date_due': _date, 'payment_term_id': self.payment_term_id.id})
                inv_created = inv_obj.create(inv_vals)
                inv_line_vals = self._prepare_invoice_line(qty, amt, origin=origin)
                inv_line_vals.update({'invoice_id': inv_created.id})
                self.env['account.invoice.line'].create(inv_line_vals)
                inv_created.update({'member_id': self.id})
                line_no += 1
        else:
            origin = 'INV - %s - %s ' % (self.partner_id.name, self.trip_id.name)
            inv_vals = self._prepare_invoice(origin=origin)
            inv_created = inv_obj.create(inv_vals)
            amt = self.trip_id.fare - self.dp_amount
            inv_line_vals = self._prepare_invoice_line(qty, amt, origin=origin)
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

    @api.one
    def action_documents_create(self):
        context = self.env.context.copy()
        context.update({'create_from_buttton': True})
        templates = self.trip_id and self.trip_id.trip_template
        trip_doc_obj = self.env['trip.document']
        doc_history = self.env['partner.document.history']
        if templates:
            docs = {}
            histories = doc_history.search([('partner_id', '=', self.partner_id.id)])
            for history in histories:
                if (history.doc_type.id not in docs) or (docs.get(history.doc_type.id,) and
                   docs.get(history.doc_type.id).get('create_date') < history.create_date):
                    docs.update({history.doc_type.id: {'create_date': history.create_date, 'doc': history.doc}})
            for doc in templates.documents:
                v = {
                    'name': doc.name,
                    'member_id': self.id,
                    'attachment': docs.get(doc.doc_type.id, {}).get('doc', None),
                    'is_image': doc.doc_type.is_image,
                    'doc_type': doc.doc_type.id
                }
                trip_doc_obj.with_context(context).create(v)
        return True

    @api.one
    def action_pay_reseller(self):
        if not self.reseller or self.reseller_fee <= 0.0:
            return True
        reseller_exp_type = self.env.ref('mt_config.id_expense_type_reseller').id
        expense_obj = self.env['trip.expense']
        expense_vals = {
            'name': 'Reseller Payment - %s - %s ' % (self.reseller.name, self.trip_id.name),
            'amount': self.reseller_fee,
            'expense_type': reseller_exp_type,
            'trip_id': self.trip_id.id
        }
        created_expense = expense_obj.create(expense_vals)
        created_expense.button_confirm()
        self.is_reseller_paid = True
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
    doc_type = fields.Many2one('document.type.config', required=True)
    name = fields.Char('Document Name', required=True)


class TripDocument(models.Model):
    _name = 'trip.document'

    member_id = fields.Many2one('trip.member', string='Trip Member')
    name = fields.Char('Document Name')
    is_image = fields.Boolean('Scanned Image?')
    attachment = fields.Binary('Attachment')
    doc_type = fields.Many2one('document.type.config', required=True)

    @api.multi
    def write(self, values):
        if 'attachment' in values:
            history_obj = self.env['partner.document.history']
            partner = self.member_id.partner_id
            history_obj.create({
                'partner_id': partner.id,
                'doc_type': values.get('doc_type') or self.doc_type.id,
                'doc': values.get('attachment'),
                'name': '%s uploaded from trip member update' % (values.get('name', False) or self.name),
                })

        return super(TripDocument, self).write(values)

    @api.model
    def create(self, vals):
        if not self._context.get('create_from_buttton', False) and vals.get('member_id'):
            history_obj = self.env['partner.document.history']
            partner = self.env['trip.member'].browse(vals.get('member_id')).partner_id
            history_obj.create({
                'partner_id': partner.id,
                'doc_type': vals.get('doc_type') or self.doc_type.id,
                'doc': vals.get('attachment'),
                'name': '%s uploaded from trip member creation' % (vals.get('name', False) or self.name),
                })

        return super(TripDocument, self).create(vals)
