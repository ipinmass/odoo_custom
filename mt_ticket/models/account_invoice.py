from odoo import fields, models


import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ticket_id = fields.Many2one('mt.ticket', string='Related Ticket')


