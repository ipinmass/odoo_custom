
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

import logging

class Trip(models.Model):
    _name = 'mt.trip'

    name = fields.Char(string="Name")
    planned_date = fields.Date(string='Planned Date')
    admin = fields.Many2one('res.partner', string='Admin')
    state = fields.Selection([('open', 'Open'),('progress', 'Progress'),('done', 'Done'), ('cancel', 'Cancel')])
    member_ids = fields.One2many('trip.member', 'trip_id', string='Members')
    expenses = fields.One2many('trip.expenses', 'trip_id', string='Expenses')
    trip_template = fields.Many2one('trip.template', 'Trip Template')
    fare = fields.Float('Fare')


    @api.multi
    def action_close_registration(self):
        return self.write({'state': 'progress'})
   

class TripMember(models.Model):
    _name = 'trip.member'

    # name = fields.Char('Name', related='partner_id.name', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer', '=', True)])
    document_ids = fields.One2many('trip.document', 'member_id', string='Documents')
    dp_amount = fields.Float(string='DP Amount', digits=dp.get_precision('Product Price'))
    invoince_ids = fields.One2many('account.invoice', 'member_id', string='Invoice Lines')
    trip_id = fields.Many2one('mt.trip', string='Trip ID')
    is_document_completed = fields.Boolean('Documents Completed', readonly=True)
    is_invoice_paid = fields.Boolean('Invoiced Paid', readonly=True)
    reseller = fields.Many2one('res.partner', string="Reseller", domain=[('customer', '=', False)])
    reseller_fee = fields.Float(string='Reseller Fee', digits=dp.get_precision('Product Price'))
    
    @api.model
    def create(self, vals):

        vals = super(TripMember, self).create(vals)
        return vals

    @api.multi
    def action_show_invoice(self):
        return

    @api.multi
    def action_show_documents(self):
        return


class TripTemplate(models.Model):
    _name = 'trip.template'


    name = fields.Char('Destination')
    documents = fields.One2many('trip.document.template', 'template_id', string='Documents')


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
