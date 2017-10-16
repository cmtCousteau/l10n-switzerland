from odoo.tests import TransactionCase
from odoo.modules import get_module_resource


class TestImportPain000(TransactionCase):
    def setUp(self):
        super(TestImportPain000, self).setUp()
        self.account_pain000 = self.env['account.pain000.parser']

    def test_import_pain000_file(self):
        test_file_path = get_module_resource('l10n_ch_import_pain000',
                                             'res',
                                             'pain002p-rejected.xml')
        file_to_import = open(test_file_path, 'r')
        data = file_to_import.read()
        data = data.replace("\n", "")
        #data = data.replace(" ", ' ')

        self.account_pain000.parse(data)

        a = 10

