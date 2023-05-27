from odoo import models, fields, api, _ 
from twilio.rest import Client


class twilioWhatsapp(models.Model):
    _name = 'twilio.whatsapp'
    _description = 'Twilio Whatsapp Record'
    _rec_name = 'sender'

    sender = fields.Char('Sender')
    receiver = fields.Char('Receiver')

    body = fields.Text('Body')
    res_model = fields.Char('Model')
    res_id = fields.Integer('Model ID')

    origin = fields.Char('Source Document', compute='get_source_document', store=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ], string='Status')

    @api.depends('res_model', 'res_id')
    def get_source_document(self):
        for rec in self:
            rec.origin = '%s,%s' %(rec.res_model, rec.res_id)
    
    def action_send(self):
        for rec in self:
            account_sid = self.env.user.company_id.twilio_account_sid
            auth_token = self.env.user.company_id.twilio_auth_token
            client = Client(account_sid, auth_token)
            try:
                message = client.messages.create( 
                                        body=rec.body,
                                        from_= 'whatsapp:' + rec.sender,
                                        to= 'whatsapp:' + rec.receiver
                                    )
                rec.state = 'sent'
            except:
                rec.state = 'failed'
