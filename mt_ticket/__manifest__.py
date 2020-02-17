{
    'name': 'MA Tickets',
    'version': '0.0',
    'category': 'Customer',
    'sequence': 999,
    'summary': 'MT Tickets',
    'description': "",
    'depends': ['base','account', 'mt_customer', 'mt_trip'],
    'data': [
        'data/ticket_generic_supplier.xml',
        'views/ticket_view.xml',
        'security/ir.model.access.csv'
        
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
