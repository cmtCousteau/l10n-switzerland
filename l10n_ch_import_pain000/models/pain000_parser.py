# -*- coding: utf-8 -*-
from odoo import models

from lxml import etree


class Pain000Parser(models.AbstractModel):
    _name = 'account.pain000.parser'

    def _parse_detail(self, result, node, ns):

        payment_order_obj = self.env['account.payment.order']
        bank_payment_line_obj = self.env['bank.payment.line']
        account_bank_parser_obj = self.env[
            'account.bank.statement.import.camt.parser']
        account_payment_cancel = self.env['account.payment.cancel']

        account_bank_parser_obj.add_value_from_node(
            ns, node, './ns:OrgnlEndToEndId', result,
            'orgnl_end_to_end_id')

        account_bank_parser_obj.add_value_from_node(
            ns, node, './ns:TxSts',
            result, 'tx_sts')

        account_bank_parser_obj.add_value_from_node(
            ns, node, './ns:StsRsnInf/ns:Rsn/ns:Cd', result,
            'full_reconcile_id')

        account_bank_parser_obj.add_value_from_node(
            ns, node, './ns:StsRsnInf/ns:Rsn/ns:Cd', result,
            'full_reconcile_id')

        account_bank_parser_obj.add_value_from_node(
            ns, node, './ns:StsRsnInf/ns:AddtlInf', result,
            'add_tl_inf')

        if 'orgnl_end_to_end_id' in result:
            bank_payment_line = bank_payment_line_obj.search(
                [('name', '=', result['orgnl_end_to_end_id'])])

            if not bank_payment_line:
                return

            payment_order_obj = payment_order_obj.search(
                [('name', '=', result['orgnl_msg_id'])])

            if 'tx_sts' in result and result['tx_sts'] == 'RJCT':
                    account_payment_cancel.cancel_payment(
                        payment_order_obj,
                        bank_payment_line,
                        result)

    def parse(self, data):
        payment_order_obj = self.env['account.payment.order']
        account_bank_parser_obj = self.env[
            'account.bank.statement.import.camt.parser']

        root = etree.fromstring(data, parser=etree.XMLParser(recover=True))
        if root is not None:
            ns = root.tag[1:root.tag.index("}")]

            result = dict()

            details_nodes = root.xpath(
                './ns:CstmrPmtStsRpt/ns:OrgnlPmtInfAndSts/ns:TxInfAndSts',
                namespaces={'ns': ns})

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns'
                          ':OrgnlMsgId', result, 'orgnl_msg_id')

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns'
                          ':OrgnlMsgNmId', result, 'orgnl_msg_nm_Id')

            if len(result) > 1 and 'orgnl_msg_nm_Id' in result:
                if 'pain.001' not in result['orgnl_msg_nm_Id'] or \
                   'pain.008' not in result['orgnl_msg_nm_Id']:

                    payment_order_obj = payment_order_obj.search(
                        [('name', '=', result['orgnl_msg_id'])])

                    for node in details_nodes:
                        self._parse_detail(result, node, ns)

                    return True, payment_order_obj
        return False, None

