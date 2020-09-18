
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
        passport_type = self.env.ref('mt_config.id_document_type_passport').id
        ktp_type = self.env.ref('mt_config.id_document_type_ktp').id
        kk_type = self.env.ref('mt_config.id_document_type_kk').id
        found = None, None
        doms = [('partner_id', '=', self.id), ('doc_type', 'in', [passport_type])]
        doms2 = [('partner_id', '=', self.id), ('doc_type', 'in', [ktp_type])]
        doms3 = [('partner_id', '=', self.id), ('doc_type', 'in', [kk_type])]
        recs = self.env['partner.document.history'].search(doms)

        for r in recs:
            if (not found[0] or found[0] < r.create_date) and 'jpeg' in guess_mimetype(base64.b64decode(r.doc)).lower():
                found = r.create_date, r.doc
        if not found[1]:
            recs = self.env['partner.document.history'].search(doms2)
            for r in recs:
                if (not found[0] or found[0] < r.create_date) and 'jpeg' in guess_mimetype(base64.b64decode(r.doc)).lower():
                    found = r.create_date, r.doc
        if not found[1]:
            recs = self.env['partner.document.history'].search(doms3)
            for r in recs:
                if (not found[0] or found[0] < r.create_date) and 'jpeg' in guess_mimetype(base64.b64decode(r.doc)).lower():
                    found = r.create_date, r.doc
        if found[1]:
            # pass
            self.passport_img = found[1]

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
