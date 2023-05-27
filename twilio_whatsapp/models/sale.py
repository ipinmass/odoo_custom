from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def button_send_whasapp(self):
        for rec in self.filtered(lambda r: r.partner_id.mobile):
            whatsapp_sender = self.env.user.company_id.twilio_whatsapp_no
            body = 'Hi testing from ipin via button sale order'
            sender = 'whatsapp:' + whatsapp_sender

            twilioObj = self.env['twilio.whatsapp'].create({
                'sender': whatsapp_sender,
                'receiver': rec.partner_id.mobile,
                'body': body,
                'res_model': self._name,
                'res_id': rec.id,
                'state': 'draft'
                
            })
            try:
                twilioObj.action_send()
                rec.message_post(body='A WhatsApp message has been sent')
            except:
                _logger.info('Unable to send WhatsApp message ')


            

