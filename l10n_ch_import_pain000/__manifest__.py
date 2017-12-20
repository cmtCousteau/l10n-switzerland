{
    'name': 'Import pain001',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Monzione Marco',
    'website': 'https://www.compassion.ch',
    'category': 'Banking addons',
    'depends': [
        'account_payment_order',
        'account_bank_statement_import_camt',
        'account_payment_line_cancel',
    ],
    'data': [

    ],
    'demo': [

    ],
    'test': [
        'res/test_data.yml',
    ],
    'installable': True,
}