{
    'name': 'AM Reporting',
    'version': '1.0',
    'category': 'Reporting',
    'sequence': 99,
    'summary': 'AM Reporting',
    'description': "",
    'depends': ['base', 'mt_config', 'account', 'mt_customer', 'mt_trip', 'mt_ticket'],
    'data': [
        'views/reporting_view.xml',
        
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
