from odoo import models


class UndoPaymentLine(models.AbstractModel):
    _name = 'account.undo.payment_line'

    def undo_payment_line(self,payment_order_obj, payment_line_obj,data_supp):

        account_move_line_obj = self.env['account.move.line']
        account_move_obj = self.env['account.move']

        if payment_order_obj and payment_line_obj:
            for payment_order_line in payment_order_obj:
                move_ids = payment_order_line.ids

            for payment_line in payment_line_obj:
                move_line_id = payment_line.move_line_id.id

                account_move_line = account_move_line_obj.search(
                    [('id', '=', move_line_id)])

                move_id = account_move_line.move_id.id

                display_name = account_move_line.display_name

                account_full_reconcile_id = account_move_line.\
                    full_reconcile_id.id

                if account_full_reconcile_id:

                    # Get the counterpart move
                    account_move_reconcilied = account_move_line_obj.search([
                                                ('full_reconcile_id', '=',
                                                account_full_reconcile_id),
                                                ('move_id', '!=', move_id)])

                    account_move = account_move_obj.search([(
                        'id', '=',account_move_reconcilied.move_id.id)])
                    account_move_reconcilied.remove_move_reconcile()
                    # unpost and delete the move from the journal.
                    account_move.button_cancel()
                    account_move.unlink()

                # Delete the payment line in the payment order.
                payment_line.unlink()
                # Search if there is something left in the payment order.
                payment_line = payment_line_obj.search([('order_id',
                                                             '=',
                                                             move_ids)])
                if len(payment_line) == 0:
                    if payment_order_obj.state == 'uploaded':
                        payment_order_obj.action_done_cancel()

                if display_name:
                    if data_supp and 'add_tl_inf' in data_supp:
                        payment_order_obj.message_post(
                            display_name + " has been removed "
                                           "because : " + data_supp[
                                'add_tl_inf'])
                    else:
                        payment_order_obj.message_post(
                            display_name + " has been removed no "
                                           "reason given.")
            return True
        return False
