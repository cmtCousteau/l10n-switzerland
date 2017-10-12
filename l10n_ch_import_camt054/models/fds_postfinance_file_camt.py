from odoo import models, api

import base64
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFileCamt(models.Model):
    _inherit = 'fds.postfinance.file'

    @api.multi
    def import2bankStatements(self):

        res = True
        account_camt_parser_obj = self.env[
            'account.bank.statement.import.camt.parser']

        for pf_file in self:
            #for pf_file in fds_file:
            values = {'data_file': pf_file.data}
            bs_import_obj = self.env['account.bank.statement.import']
            bank_wiz_imp = bs_import_obj.create(values)
            decoded_file = base64.b64decode(bank_wiz_imp.data_file)
            result = account_camt_parser_obj.parse(decoded_file)

            if len(result) > 2 and result[0] is None and result[1] is \
                    None:
                pf_file.write({
                    'state': 'done',
                    'data': None,
                 })

                _logger.info("[OK] import file '%s' as an empty camt",
                             (pf_file.filename))
            else:
                res = super(FdsPostfinanceFileCamt,
                            self).import2bankStatements()
        return res



