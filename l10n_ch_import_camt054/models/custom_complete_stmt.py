from odoo import api, models


class AccountStatementImportCustomCamt053(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @api.model
    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """
        Use completion rules in journal to find missing partners.
        """
        stmts_vals = super(AccountStatementImportCustomCamt053, self)._complete_stmts_vals(
            stmts_vals, journal, account_number)

        list_transactions = stmts_vals[0]['transactions']

        for transaction in list_transactions:
            if transaction['sub_fmly_cd'] == 'RRTN':
                for trans in list_transactions:
                    if trans['ref'] == transaction['ref'] and trans != transaction:
                        trans['account_id'] = transaction['account_id']



        return stmts_vals