from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Company(models.Model):
    _inherit = 'res.company'

    watermark_img = fields.Binary('Watermark Image', help='Image used for watermark in qweb reporting')