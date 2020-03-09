from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import date

import logging
_logger = logging.getLogger(__name__)

class TripExpense(models.Model):
    _inherit = 'trip.expense'

    ticket_id = fields.Many2one('mt.ticket', string='Related Ticket')
    policy_number = fields.Char('Policy Number')
    expense_type_name = fields.Char('Name of Expense Type', related='expense_type.name')

    @api.model
    def default_get(self,default_fields):
        res = super(TripExpense, self).default_get(default_fields)

        if self._context.get('ticket_id'):
            res['expense_type'] = self.env.ref('mt_config.id_expense_type_insurance').id
        return res


    def _get_name(self):
        self.ensure_one()
        if self.ticket_id:
            r = self.ticket_id and self.ticket_id.name or ''
            return r
        else:
            return super(TripExpense, self)._get_name()
            
    
    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        if not self._context.get('ticket_id'):
            return super(TripExpense, self)._onchange_expense_type()
        insurance = self.env.ref('mt_config.id_expense_type_insurance').id

        domain = {'expense_type': [('id', 'in', [insurance])]}
        return {'domain': domain}
    
    @api.one
    def issue_invoice_from_model(self): 
        _logger.info('========= _context issue issue_invoice %s', self._context)
        if not self._context.get('ticket_id', False):
            return super(TripExpense, self).issue_invoice_from_model()
        model = ('ticket_id', self._context.get('ticket_id'))
        _logger.info('========= _context model ticket %s', model)
        self.partner_id = self.ticket_id.partner_id
        self.issue_invoice(model)