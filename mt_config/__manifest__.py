{
    'name': 'AM Configuration',
    'version': '12.0',
    'category': 'Configuration',
    'sequence': 99,
    'summary': 'AM Configuration ',
    'description': "",
    'depends': ['base'],
    'data': [
        'data/am_group_config.xml',
        'data/document_type_data.xml',
        'data/expense_type_data.xml',
        'views/document_type_view.xml',
        'views/expense_type_view.xml',
        'security/ir.model.access.csv',
        
        
    ],
    'demo': [
        
    ],
    'installable': True,
    'application': True,
    'qweb': [''],
    'website': '',
}
