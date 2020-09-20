
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
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    passport_no = fields.Char('Passport No', related='partner_id.passport_no')
    passport_img = fields.Binary('Scanned Passport', related='partner_id.passport_img')
    passport_exp = fields.Date('Passport Validity', related='partner_id.passport_exp')
    passport_issued = fields.Date('Passport Issued', related='partner_id.passport_issued')
    dtof_birth = fields.Date('Date of Birth', related='partner_id.dtof_birth')
    trip_id_personal = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    insurance_invoiced = fields.Boolean('Insurance Invoiced ?', default=False, readonly=True)

    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        context = self._context or {}
        # if context.get('trip_id'):
        #     query = '''
        #         SELECT partner_id FROM trip_member WHERE trip_id=%s
        #     ''' % context.get('trip_id')
        #     self.env.cr.execute(query)
        #     res = self.env.cr.dictfetchall()

        if context.get('personal', None) is not None:
            domain = {'expense_type': [('personal', '=', context.get('personal'))]}
            return {'domain': domain}

    def _get_name(self):
        self.ensure_one()
        if self.trip_id:
            return self.trip_id and self.trip_id.name or ''
        else:
            return ''

    @api.one
    def issue_invoice(self, model):
        if self.expense_type.name.lower() == 'insurance' and self.partner_id:
            inv_obj = self.env['account.invoice']
            journal_id = self.env.ref('mt_trip.mt_journal_customer_payment_id').id
            vinvoice = self.env['account.invoice'].new({'partner_id': self.partner_id.id})
            # Get partner extra fields
            vinvoice._onchange_partner_id()
            inv_vals = vinvoice._convert_to_write(vinvoice._cache)

            inv_vals.update({
                'name': 'insurance Invoice - ' + self.name,
                'origin': self.name or '',
                'type': 'out_invoice',
                'account_id': self.partner_id.property_account_receivable_id.id,
                'journal_id': journal_id,
                'currency_id': self.env.user.company_id.currency_id.id,
                'company_id': self.env.user.company_id.id,
                'user_id': self.env.user.id,
                'partner_id': self.partner_id.id,
                'date_invoice': fields.Date.today(),
                model[0]: model[1]
            })
            created_inv = inv_obj.create(inv_vals)

            inv_lines = {
                'name': self.partner_id.name,
                'origin': self.name,
                'account_id': self.partner_id.property_account_receivable_id.id,
                'price_unit': self.amount,
                'quantity': 1,
                'discount': 0.0,
                'invoice_id': created_inv.id
                }
            self.env['account.invoice.line'].create(inv_lines)
            self.insurance_invoiced = True

    @api.one
    def issue_invoice_from_model(self):
        model = None
        if self._context.get('trip_id', False):
            model = ('trip_id_personal', self._context.get('trip_id'))
        if not model:
            return True
        self.issue_invoice(model)

    @api.one
    def button_confirm(self):
        # ctx = self._context
        inv_obj = self.env['account.invoice']
        partner_id = self.env.ref('mt_trip.supplier_generic_ma_travel')
        journal_id = self.env.ref('mt_trip.mt_journal_payment_id').id
        company_id = self.env.user.company_id
        if self.expense_type.name and self.expense_type.name.lower() == 'tax':
            partner_id = self.env.ref('mt_trip.supplier_tax_generic_ma_travel')
            journal_id = self.env.ref('mt_trip.mt_journal_tax_payment_id').id
        if not all([partner_id, journal_id]):
            return True

        vinvoice = self.env['account.invoice'].new({'partner_id': partner_id.id})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)

        name = self._get_name()
        _logger.info('fafhaskfdddd---------- name %s', name)
        name = isinstance(name, list) and name[0] or name
        invoice_vals = {
            'name': 'Sup Invoice - ' + str(name),
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
        self.invoice_id = inv_created
        inv_created.action_invoice_open()
        return True
