
from odoo import api, fields, models
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    member_id = fields.Many2one('trip.member', string='Related Member')
    payment_proof = fields.Binary(string='Payment Proof')
    payment_proof_img = fields.Binary(string='Payment Proof Preview', readonly=True, default=False)
    payment_proof_ids = fields.One2many('payment.proof', 'invoice_id', string='Payment Proofs')
    is_downpayment = fields.Boolean('Down Payment Invoice', default=False)

    # @api.multi
    # def write(self, values):
    #     if 'payment_proof' in values:
    #         if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
    #             values.update({'payment_proof_img': values.get('payment_proof')})
    #         else:
    #             values.update({'payment_proof_img': False})
    #     return super(AccountInvoice, self).write(values)

    # @api.model
    # def create(self, values):
    #     if 'payment_proof' in values:
    #         if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
    #             values.update({'payment_proof_img': values.get('payment_proof')})
    #         else:
    #             values.update({'payment_proof_img': False})
    #     return super(AccountInvoice, self).create(values)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_item = fields.Char('Item')


class PaymentProof(models.Model):
    _name = 'payment.proof'

    name = fields.Char('Description')
    create_date = fields.Datetime('Created on', index=True, readonly=True)
    payment_proof = fields.Binary('Attachment')
    payment_proof_img = fields.Binary('Attachment Preview', readonly=True, default=False)
    invoice_id = fields.Many2one('account.invoice', string='Related Invoice')

    @api.multi
    def write(self, values):
        if 'payment_proof' in values:
            if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
                values.update({'payment_proof_img': values.get('payment_proof')})
            else:
                values.update({'payment_proof_img': False})
        return super(PaymentProof, self).write(values)

    @api.model
    def create(self, values):
        if 'payment_proof' in values:
            if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
                values.update({'payment_proof_img': values.get('payment_proof')})
            else:
                values.update({'payment_proof_img': False})
        return super(PaymentProof, self).create(values)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_proof = fields.Binary('Payment Proof')
    is_downpayment = fields.Boolean(string='Payment for Down Payment')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        invoice = invoice_defaults[0]
        rec['is_downpayment'] = invoice['is_downpayment']
        return rec

    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()
        for rec in self:
            invoice = rec.invoice_ids and rec.invoice_ids[0]
            if not invoice.is_downpayment:
                if not rec.payment_proof and invoice.type == 'out_invoice':
                    raise ValidationError('You have to upload a payment proof for this payment')

                # invoice.payment_proof = rec.payment_proof
                else:
                    self.env['payment.proof'].create({'invoice_id': invoice.id,
                                                      'payment_proof': rec.payment_proof,
                                                      'name': 'Payment Registration', })
        return res
