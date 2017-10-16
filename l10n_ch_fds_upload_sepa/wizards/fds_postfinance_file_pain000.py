from odoo import models, api

import base64
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFilePain000(models.Model):
    _inherit = 'fds.postfinance.file'

    @api.multi
    def import2bankStatements(self):

        account_pain000 = self.env['account.pain000.parser']
        pain_files = self.env[self._name]

        for pf_file in self:
            try:
                decoded_file = base64.b64decode(pf_file.data)

                result = account_pain000.parse(decoded_file)

                if result[0]:
                    if result[1] is not None and result[1].id:
                        # Link the payment order to the file import.
                        pf_file.payment_order = result[1].id
                        # Attach the file to the payment order.
                        self.env['ir.attachment'].create({
                                'datas_fname': pf_file.filename,
                                'res_model': 'account.payment.order',
                                'datas': pf_file.data,
                                'name': pf_file.filename,
                                'res_id': result[1].id})

                    pf_file.write({
                        'state': 'done',
                        'data': pf_file.data
                    })

                    _logger.info("[OK] import file '%s' as pain.000",
                                 pf_file.filename)

                    pain_files += pf_file
            except:
                pf_file._state_error_on()
                _logger.warning("[FAIL] import file '%s' as pain 000",
                                (pf_file.filename))

        return super(FdsPostfinanceFilePain000, self-pain_files).import2bankStatements()
