
from odoo import api, fields, models

import logging

class Trip(models.Model):
    _name = 'ma.trip'

    name = fields.Char(string="Nmae")
    state = fields.Selection([('draft', 'Draft'),('progress', 'Progress'),('done', 'Done'), ('cancel', 'Cancel')])
    members = fields.One2many('res.partner', 'trip_id', string='Members')
    expenses = fields.One2many('trip.expenses', 'trip_id', string='Expenses')
    trip_template = fields.Many2one('trip.template', 'Trip Template')


    @api.multi
    def action_trip_validate(self):
    	return self.write({'state': 'progress'})
   

class TripMember(models.Model):
	_name = 'trip.member'

	name = fields.Char('Name', related='partner_id.name', readonly=True)
	partner_id = fields.Many2one('res.partner', 'Related Partner')
	document_ids = fields.One2many('tip.document', 'member_id', string='Documents')
	dp_amount = fields.Float('DP Amount')
	invoince_ids = fields.One2many('account.invoice', 'member_id', string='Invoice Lines')
	
	@api.model
	def create(self, vals):

		vals = super(TripMember).create(vals)
		return vals

	@api.multi
	def action_show_invoice():
		return

	@api.multi
	def action_show_documents():
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
	is_image = fields.Boolean('Scanned Image?')
	attachment = fields.Binary('Attachment')