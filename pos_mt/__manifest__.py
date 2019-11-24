# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': '',
    'version': '1.2.0',
    'category': 'Point Of Sale',
    'sequence': 40,
    'summary': 'Odoo PoS Modification',
    'description': "",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_mt_templates.xml',
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/pos.xml'],
    'website': '',
}
