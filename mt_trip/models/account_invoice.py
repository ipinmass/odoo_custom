
from odoo import api, fields, models
from odoo.tools.mimetypes import guess_mimetype
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    member_id = fields.Many2one('trip.member', strint='Member Payments')
    payment_proof = fields.Binary(string='Payment Proof')
    payment_proof_img = fields.Binary(string='Payment Proof Preview', readonly=True, default=False)

    @api.multi
    def write(self, values):
        if 'payment_proof' in values:
            if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
                values.update({'payment_proof_img': values.get('payment_proof')})
            else:
                values.update({'payment_proof_img': False})
        return super(AccountInvoice, self).write(values)

    @api.model
    def create(self, values):
        if 'payment_proof' in values:
            if values.get('payment_proof') and 'jpeg' in guess_mimetype(base64.b64decode(values.get('payment_proof'))).lower():
                values.update({'payment_proof_img': values.get('payment_proof')})
            else:
                values.update({'payment_proof_img': False})
        return super(AccountInvoice, self).create(values)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_item = fields.Char('Item')
