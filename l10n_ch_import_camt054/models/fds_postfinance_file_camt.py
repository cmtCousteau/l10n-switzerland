from odoo import models, api

import base64
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFileCamt(models.Model):
    _inherit = 'fds.postfinance.file'

    @api.multi
    def import2bankStatements(self):

        camt_files = self.env[self._name]
        account_camt_parser_obj = self.env[
            'account.bank.statement.import.camt.parser']

        for pf_file in self:
            try:
                decoded_file = base64.b64decode(pf_file.data)

                result = account_camt_parser_obj.parse(decoded_file)

                if len(result) > 2 and result[0] is None and result[1] is \
                        None:
                    pf_file.write({
                        'state': 'done',
                        'data': pf_file.data,
                     })

                    _logger.info("[OK] import file '%s' as an empty camt",
                                 pf_file.filename)
                    camt_files += pf_file
            except:
                pf_file.write({'state': 'error'})
                _logger.warning("[FAIL] import file '%s' as an empy camt",
                                (pf_file.filename))

        return super(FdsPostfinanceFileCamt, self -
                     camt_files).import2bankStatements()



