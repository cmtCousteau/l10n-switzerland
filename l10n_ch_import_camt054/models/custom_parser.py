import re

from odoo import models


class customParser(models.AbstractModel):
    _inherit = 'account.bank.statement.import.camt.parser'

    def parse_entry(self, ns, node):
        """Parse an Ntry node and yield transactions"""
        bank_payment_line_obj = self.env['bank.payment.line']
        payment_line_obj = self.env['account.payment.line']
        undo_payment_line_obj = self.env['account.undo.payment_line']

        test = dict()

        transaction = {'name': '/', 'amount': 0}  # fallback defaults
        self.add_value_from_node(
            ns, node, './ns:BkTxCd/ns:Prtry/ns:Cd', transaction,
            'transfer_type'
        )
        self.add_value_from_node(
            ns, node, './ns:BookgDt/ns:Dt', transaction, 'date')
        self.add_value_from_node(
            ns, node, './ns:BookgDt/ns:Dt', transaction, 'execution_date')
        self.add_value_from_node(
            ns, node, './ns:ValDt/ns:Dt', transaction, 'value_date')
        amount = self.parse_amount(ns, node)
        if amount != 0.0:
            transaction['amount'] = amount
        self.add_value_from_node(
            ns, node, './ns:AddtlNtryInf', transaction, 'name')
        self.add_value_from_node(
            ns, node, [
                './ns:NtryDtls/ns:RmtInf/ns:Strd/ns:CdtrRefInf/ns:Ref',
                './ns:NtryDtls/ns:Btch/ns:PmtInfId',
                './ns:NtryDtls/ns:TxDtls/ns:Refs/ns:AcctSvcrRef'
            ],
            transaction, 'acct_svcr_ref'
        )



        details_nodes = node.xpath(
            './ns:NtryDtls/ns:TxDtls', namespaces={'ns': ns})
        if len(details_nodes) == 0:
            yield transaction
            self.add_value_from_node(
                ns, node, './ns:AcctSvcrRef', transaction, 'acct_svcr_ref')
            return

        self.add_value_from_node(
            ns,
            node,
            './ns:BkTxCd/ns:Domn/ns:Fmly/ns:SubFmlyCd',
            test,
            'sub_fmly_cd')

        self.add_value_from_node(
            ns,
            node,
            './ns:NtryDtls/ns:TxDtls/ns:Refs/ns:EndToEndId',
            test,
            'EndToEndId')

        inf = dict()

        transaction['sub_fmly_cd'] = test['sub_fmly_cd']

        if test['sub_fmly_cd'] == 'RRTN':
            bank_payment_line = bank_payment_line_obj.search(
                [('name', '=', test['EndToEndId'])])

            payment_line = payment_line_obj.search(
                [('bank_line_id', '=', bank_payment_line.id)])

            payment_order = bank_payment_line.order_id
            inf['add_tl_inf'] = transaction['name']

            account_payment_mode = payment_order.payment_mode_id

            if account_payment_mode.offsetting_account == 'bank_account':
                te = True

            if account_payment_mode.offsetting_account == 'transfer_account':
                transfer_account = account_payment_mode.transfer_account_id
                account_code = transfer_account.code
                transaction['account_id'] = transfer_account.id


            undo_payment_line_obj.undo_payment_line(payment_order,
                                                      payment_line,
                                                      inf)

        transaction_base = transaction
        for node in details_nodes:
            transaction = transaction_base.copy()
            self.parse_transaction_details(ns, node, transaction)
            yield transaction

    def parse_transaction_details(self, ns, node, transaction):
        super(customParser, self).parse_transaction_details(
            ns, node, transaction)
        # Check if a global AcctSvcrRef exist
        found_node = node.xpath('../../ns:AcctSvcrRef', namespaces={'ns': ns})
        if len(found_node) != 0:
            self.add_value_from_node(
                ns, node, '../../ns:AcctSvcrRef', transaction,
                'acct_svcr_ref')
        else:
            self.add_value_from_node(ns, node, './ns:Refs/ns:AcctSvcrRef',
                                     transaction,'acct_svcr_ref')

    def parse_statement(self, ns, node):

        result = {}
        entry_nodes = node.xpath('./ns:Ntry', namespaces={'ns': ns})

        if len(entry_nodes) > 0:
            result = super(customParser, self).parse_statement(ns, node)

            entry_ref = node.xpath('./ns:Ntry/ns:NtryRef', namespaces={
                'ns': ns})
            if len(entry_ref) > 1:
                first_entry = entry_ref[0].text
                #Parse all entry ref node to check if they're all the same.
                for entry in entry_ref:
                    if first_entry != entry.text:
                        raise ValueError('Different entry ref in same file '
                                         'not supported !')
            self.add_value_from_node(
                ns, node, './ns:Ntry/ns:NtryRef', result, 'ntryRef')
            result['camt_headers'] = ns
        # In case of an empty camt file
        else:
            transactions = []
            result['transactions'] = ''
            result['is_empty'] = True
        return result

    def parse(self, data):

        result = super(customParser, self).parse(data)
        currency = result[0]
        account_number = result[1]
        statements = result[2]
        if len(statements) > 0:
            if 'camt_headers' in statements[0]:
                if 'camt.053' not in statements[0]['camt_headers']:
                    if 'ntryRef' in statements[0]:
                        account_number = statements[0]['ntryRef']
        return currency, account_number, statements

    def get_balance_amounts(self, ns, node):
        result = super(customParser, self).get_balance_amounts(ns, node)
        start_balance_node = result[0]
        end_balance_node = result[0]

        details_nodes = node.xpath(
            './ns:Bal/ns:Amt', namespaces={'ns': ns})

        if start_balance_node == 0.0 and not len(details_nodes):
            start_balance_node = node.xpath('./ns:Ntry', namespaces={'ns':
                                                                         ns})
            amount_tot = 0
            for node in start_balance_node:
                amount_tot -= self.parse_amount(ns, node)
            return (
                amount_tot,
                end_balance_node
            )
        return result

    def check_version(self, ns, root):
        try:
            super(customParser, self).check_version(ns, root)
        except ValueError:
            re_camt_version = re.compile(
                r'(^urn:iso:std:iso:20022:tech:xsd:camt.054.'
                r'|^ISO:camt.054.)'
            )
            if not re_camt_version.search(ns):
                raise ValueError('no camt 052 or 053 or 054: ' + ns)
            # Check GrpHdr element:
            root_0_0 = root[0][0].tag[len(ns) + 2:]  # strip namespace
            if root_0_0 != 'GrpHdr':
                raise ValueError('expected GrpHdr, got: ' + root_0_0)

