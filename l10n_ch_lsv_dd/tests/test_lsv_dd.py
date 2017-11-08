# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2017 Emanuel Cino
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields
from odoo.tests import TransactionCase


class TestLsvDD(TransactionCase):

    def setUp(self):
        super(TestLsvDD, self).setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'bank')], limit=1)
        self.account_receivable = self.env['account.account'].search([
            ('code', '=', '1100')], limit=1)
        self.product_account = self.env['account.account'].search([
            ('code', '=', '3200')], limit=1)
        self.product = self.env.ref('product.product_product_10')

        # Payment modes
        self.paymode_lsv = self.env.ref('l10n_ch_lsv_dd.lsv_pay_mode')
        self.paymode_dd = self.env.ref('l10n_ch_lsv_dd.dd_pay_mode')
        self.paymode_dd_xml = self.env.ref('l10n_ch_lsv_dd.dd_pay_mode_xml_dd')

        # Bank accounts
        self.lsv_bank_account = self.env.ref('l10n_ch_lsv_dd.company_bank_ubs')
        self.dd_bank_account = self.env.ref('l10n_ch_lsv_dd.company_bank_post')
        self.dd_xml_bank_account = self.env.ref(
            'l10n_ch_lsv_dd.company_bank_post_xml_dd')

        # Mandates
        self.lsv_mandate = self.env.ref('l10n_ch_lsv_dd.ubs_mandate')
        self.dd_mandate = self.env.ref('l10n_ch_lsv_dd.post_mandate')
        self.dd_xml_mandate = self.env.ref(
            'l10n_ch_lsv_dd.post_mandate_xml_dd')

        # Create some invoices that will be included in payment orders
        self.lsv_invoice = self.create_invoice(
            self.paymode_lsv.id,
            self.lsv_bank_account.id,
            self.lsv_mandate.id,
            42)
        self.dd_invoice = self.create_invoice(
            self.paymode_dd.id,
            self.dd_bank_account.id,
            self.dd_mandate.id,
            48)
        self.dd_xml_invoice = self.create_invoice(
            self.paymode_dd_xml.id,
            self.dd_xml_bank_account.id,
            self.dd_xml_mandate.id,
            56)

    def create_invoice(self, payment_mode_id, partner_bank_id, mandate_id,
                       amount):
        """
        Utility to quickly create an invoice
        """
        vals = {
            'company_id': self.env.ref('base.main_company').id,
            'journal_id': self.journal.id,
            'currency_id': self.env.ref('base.CHF').id,
            'account_id': self.account_receivable.id,
            'type': 'out_invoice',
            'partner_id': self.partner.id,
            'date_invoice': fields.Date.today(),
            'partner_bank_id': partner_bank_id,
            'mandate_id': mandate_id,
            'bvr_reference': '42564984',
            'payment_mode_id': payment_mode_id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'account_id': self.product_account.id,
                'name': self.product.name,
                'price_unit': amount,
                'quantity': 1,
            })]
        }
        invoice = self.env['account.invoice'].create(vals)
        invoice.action_invoice_open()
        return invoice

    def create_payment_order(self, payment_mode, move_line, bank_id,
                             partner_bank_id, mandate_id):
        return self.env['account.payment.order'].create({
            'date_prefered': 'due',
            'payment_mode_id': payment_mode.id,
            'journal_id': payment_mode.fixed_journal_id.id,
            'company_partner_bank_id': bank_id,
            'payment_type': 'inbound',
            'state': 'draft',
            'payment_line_ids': [(0, 0, {
                'move_line_id': move_line.id,
                'amount_currency': move_line.debit,
                'currency_id': self.env.ref('base.CHF').id,
                'partner_id': self.partner.id,
                'partner_bank_id': partner_bank_id,
                'mandate_id': mandate_id,
                'communictation_type': 'normal',
                'communication': '42564984'
            })]
        })

    def test_lsv_payment_order(self):
        """
        Test the generation of a LSV payment file
        """
        move_line = self.lsv_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_lsv, move_line, self.lsv_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_ubs').id,
            self.lsv_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)

    def test_dd_payment_order(self):
        """
        Test the generation of a DD payment file
        """
        move_line = self.dd_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd, move_line, self.dd_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_post').id,
            self.dd_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)

    def test_dd_xml_payment_order(self):
        """
        Test the generation of a DD XML payment file
        """
        move_line = self.dd_xml_invoice.move_id.line_ids[0]
        pay_order = self.create_payment_order(
            self.paymode_dd_xml, move_line, self.dd_xml_bank_account.id,
            self.env.ref('l10n_ch_lsv_dd.partner_bank_post_xml_dd').id,
            self.dd_xml_mandate.id
        )
        pay_order.draft2open()
        result = pay_order.open2generated()
        attachment_id = result.get('res_id')
        self.assertTrue(attachment_id)
        attachment = self.env['ir.attachment'].browse(attachment_id)
        self.assertTrue(attachment.datas)
