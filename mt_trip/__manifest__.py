{
    'name': 'MA Trip',
    'version': '10.0',
    'category': 'Customer',
    'sequence': 999,
    'summary': 'MT TRIP',
    'description': "",
    'depends': ['base','account', 'mt_customer'],
    'data': [
        'data/accounting_data.xml',
        'data/company_data.xml',
        'views/trip_view.xml',
        'views/invoice_view.xml',
        'views/account_payment_view.xml',
        'security/ir.model.access.csv'
        
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
