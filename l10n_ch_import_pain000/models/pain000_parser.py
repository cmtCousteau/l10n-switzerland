from odoo import models

from lxml import etree


class Pain000Parser(models.AbstractModel):
    _name = 'account.pain000.parser'

    def parse(self, data):
        payment_order_obj = self.env['account.payment.order']
        payment_line_obj = self.env['account.payment.line']
        account_bank_parser_obj = self.env[
            'account.bank.statement.import.camt.parser']
        undo_payment_line_obj = self.env['account.undo.payment_line']

        root = etree.fromstring(data, parser=etree.XMLParser(recover=True))
        if root is not None:
            ns = root.tag[1:root.tag.index("}")]

            result = dict()

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns'
                          ':OrgnlMsgId', result, 'orgnl_msg_id')
            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlGrpInfAndSts/ns'
                          ':OrgnlMsgNmId', result, 'orgnl_msg_nm_Id')
            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlPmtInfAndSts/ns'
                          ':TxInfAndSts/ns:OrgnlEndToEndId', result,
                'orgnl_end_to_end_id')

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt'
                          '/ns:OrgnlPmtInfAndSts/ns:TxInfAndSts/ns:TxSts',
                result, 'tx_sts')

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlPmtInfAndSts/ns'
                          ':TxInfAndSts/ns:StsRsnInf/ns:Rsn/ns:Cd', result,
                'full_reconcile_id')
            account_bank_parser_obj.add_value_from_node(
                ns, root,
                './ns:CstmrPmtStsRpt/ns:OrgnlPmtInfAndSts/'
                'ns:StsRsnInf/ns:Rsn/ns:Cd',
                result,
                'full_reconcile_id')

            account_bank_parser_obj.add_value_from_node(
                ns, root, './ns:CstmrPmtStsRpt/ns:OrgnlPmtInfAndSts/ns'
                          ':TxInfAndSts/ns:StsRsnInf/ns:AddtlInf', result,
                'add_tl_inf')

            if len(result) > 1 and 'orgnl_msg_nm_Id' in result:
                if 'pain.001' not in result['orgnl_msg_nm_Id'] or \
                   'pain.008' not in result['orgnl_msg_nm_Id']:

                    if 'orgnl_msg_id' in result:
                        payment_order_obj = payment_order_obj.search(
                            [('name', '=', result['orgnl_msg_id'])])

                    if 'orgnl_end_to_end_id' in result:
                        payment_line_obj = payment_line_obj.search(
                            [('name', '=', result['orgnl_end_to_end_id'])])

                    if 'TxSts' in result:
                        if result['tx_sts'] == 'RJCT':
                            if undo_payment_line_obj.undo_payment_line(
                                                payment_order_obj,
                                                payment_line_obj,
                                                result):
                                return True, None
                    return True, payment_order_obj
        return False, None
