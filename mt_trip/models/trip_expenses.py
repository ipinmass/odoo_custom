
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
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
    state = fields.Selection(string='State', related='invoice_id.state', readonly=True, derault=None)
    trip_id = fields.Many2one('mt.trip', string='Related Trip')
    code = fields.Char('Code', help='Can be either Hotel Code or Flight Code, depending on the Expense Type')
    personal = fields.Boolean(string='Is Personal Expense?', related='expense_type.personal')
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    passport_no = fields.Char('Passport No', related='partner_id.passport_no')
    passport_img = fields.Binary('Scanned Passport', related='partner_id.passport_img')
    passport_exp = fields.Date('Passport Validity', related='partner_id.passport_exp')
    passport_issued = fields.Date('Passport Issued', related='partner_id.passport_issued')
    ktp_no = fields.Char('KTP', related='partner_id.ktp_no')
    dtof_birth = fields.Date('Date of Birth', related='partner_id.dtof_birth')
    trip_id_personal = fields.Many2one('mt.trip', string='Related Trip')
    insurance_invoiced = fields.Boolean('Insurance Invoiced ?', default=False, readonly=True)


    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        context = self._context or {}

        if context.get('personal', None) is not None:
            domain = {'expense_type': [('personal', '=', context.get('personal'))]}
            return {'domain': domain}

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        context = self.env.context.copy() or {}
        trip_id = context.get('trip_id')
        partner_ids = []
        if trip_id:
            for member in self.env['mt.trip'].browse(trip_id).member_ids:
                partner_ids.append(member.partner_id.id)
        domain = {'partner_id': [('id', 'in', partner_ids)]}
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
            expense_acc = self.env.ref('mt_trip.default_partner_account_expense').id
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
                'account_id': expense_acc,
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
        hotel_expense_type = self.env.ref('mt_config.id_expense_type_hotel').id
        flight_expense_type = self.env.ref('mt_config.id_expense_type_flight').id

        if self.state and self.state != 'draf':
            raise ValidationError('Payment status is %s now, please check the related invoice down below' % (self.state))
        # ctx = self._context
        expense_acc = self.env.ref('mt_trip.default_partner_account_expense').id
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
            'account_id': expense_acc,
            'price_unit': self.amount,
            'quantity': 1,
            'discount': 0.0,
        }
        inv_created = inv_obj.create(invoice_vals)

        invoice_line_vals.update({'invoice_id': inv_created.id})
        self.env['account.invoice.line'].create(invoice_line_vals)
        self.invoice_id = inv_created
        inv_created.action_invoice_open()
        if self._context.get('params', {}).get('id', False):
            trip = self.env['mt.trip'].browse(self._context.get('params').get('id'))
            rel_member = [m for m in trip.member_ids if m.partner_id == self.partner_id]
            if len(rel_member) > 0:
                rel_member = rel_member[0]
            if not rel_member or not self.code:
                return True
            if self.expense_type.id == hotel_expense_type:
                rel_member.hotel_code = self.code
            elif self.expense_type.id == flight_expense_type:
                rel_member.flight_code = self.code
            else:
                pass

        return True

    @api.multi
    def action_invoice_show(self):
        invoices = self.invoice_id
        action_vals = {
            'name': _('Invoices'),
            'domain': [('id', 'in', [invoices.id])],
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
