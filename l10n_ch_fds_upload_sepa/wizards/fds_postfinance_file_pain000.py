from odoo import models, api

import base64
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFilePain000(models.Model):
    _inherit = 'fds.postfinance.file'

    @api.multi
    def import2bankStatements(self):
        res = True
        account_pain000 = self.env['account.pain000.parser']
        for pf_file in self:
            values = {'data_file': pf_file.data}
            bs_import_obj = self.env['account.bank.statement.import']
            bank_wiz_imp = bs_import_obj.create(values)

            decoded_file = base64.b64decode(bank_wiz_imp.data_file)
            result = account_pain000.parse(decoded_file)
            if result[0]:
                if result[1] is not None and result[1].id:
                    # Link the payment order to the file import.
                    pf_file.payment_order = result[1].id
                    # Attach the file to the payment order.
                    self.env['ir.attachment'].create({
                            'datas_fname': pf_file.filename,
                            'res_model': 'account.payment.order',
                            'datas': bank_wiz_imp.data_file,
                            'name': pf_file.filename,
                            'res_id': result[1].id})

                pf_file.write({
                    'state': 'done',
                    'data': bank_wiz_imp.data_file
                })

                _logger.info("[OK] import file '%s' as pain.000",
                             pf_file.filename)
            else:
                res = super(FdsPostfinanceFilePain000,
                            self).import2bankStatements()
        return res
