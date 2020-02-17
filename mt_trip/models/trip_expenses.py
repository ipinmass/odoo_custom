
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


