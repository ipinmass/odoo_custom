
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
# import mimetypes
import base64
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class Partner(models.Model):

    _inherit = 'res.partner'

    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", default='male', required=True)
    dtof_birth = fields.Date(string='Date of Birth')
    passport_no = fields.Char(string='Passport Number')
    passport_exp = fields.Date(string='Passport Validity')
    passport_issued = fields.Date(string='Passport Issued Date')
    document_history = fields.One2many('partner.document.history', 'partner_id', string='Document Histories')
    passport_img = fields.Binary(compute='get_passport', string='Passport', store=True)
    reseller_id = fields.Many2one('res.partner', string='Reseller')

    @api.one
    @api.depends('document_history', 'document_history.doc')
    def get_passport(self):
        found = None, None
        for history in self.document_history:
            decoded_value = base64.b64decode(history.doc)
            if ('passport' in history.doc_type.name.lower()) and ('image' in guess_mimetype(decoded_value).lower()):
                # _logger.info("1===================Found %s", history.name)
                if history.create_date:
                    if not found[0] or found[0] < history.create_date:
                        found = history.create_date, history.doc
        if found[1]:
            self.passport_img = found[1]
            # decoded_value = base64.b64decode(found[1])
            # _logger.info("===================Found %s", guess_mimetype(decoded_value))

    @api.one
    @api.constrains('passport_no')
    def _check_passport(self):
        if self.passport_no:  # Allowing to register empty passport number
            records = self.search([('passport_no', '=', self.passport_no), ('id', '!=', self.id)])
            for rec in records:
                raise ValidationError(_("This passport number has been used by another person, named: %s" % rec.name))


class DocumentHisotry(models.Model):
    _name = 'partner.document.history'
    _order = 'create_date desc'

    create_date = fields.Datetime('Created on', index=True, readonly=True)
    name = fields.Char('Name', required=True)
    doc_type = fields.Many2one('document.type.config', string='Document Type', required=True)
    doc = fields.Binary('Attachment', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
