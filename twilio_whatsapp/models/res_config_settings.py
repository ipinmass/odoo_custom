# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    twilio_account_sid = fields.Char('Twilio Account SID')
    twilio_auth_token = fields.Char('Twilio Auth Token')
    twilio_whatsapp_no = fields.Char('Twilio WhatsApp Number')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    twilio_account_sid = fields.Char(related="company_id.twilio_account_sid", string='Twilio Account SID', readonly=False)
    twilio_auth_token = fields.Char('Twilio Auth Token', related="company_id.twilio_auth_token", readonly=False)
    twilio_whatsapp_no = fields.Char('Twilio WhatsApp Number', related="company_id.twilio_whatsapp_no", readonly=False)
