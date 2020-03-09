{
    'name': 'AM Customer',
    'version': '10.0',
    'category': 'Customer',
    'sequence': 99,
    'summary': 'Customer Additional Information',
    'description': "",
    'depends': ['base', 'mt_config', 'account', ],
    'data': [
        'views/partner_view.xml',
        'security/ir.model.access.csv',
        
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
