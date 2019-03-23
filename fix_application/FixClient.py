import sys, random, argparse, math

import quickfix as fix

from pkg.common.Order import *
from pkg.common.Trade import Trade
from pkg.qf_map import *


class FixClient(fix.Application):

    traders = {}

    def onCreate(self, sessionID):
        return

    def onLogon(self, sessionID):
        self.sessionID = sessionID
        print("Successful Logon to session '%s'." % sessionID.toString())
        return

    def onLogout(self, sessionID):
        return

    def toAdmin(self, sessionID, message):
        return

    def fromAdmin(self, sessionID, message):
        return

    ####################################################################################################################

    def toApp(self, message: fix.Message, sessionID: fix.SessionID):
        # print("\nSending message: %s" % message.toString())
        return

    def create_default_message(self):
        message = fix.Message()
        message.getHeader().setField(fix.BeginString(fix.BeginString_FIXT11))

        return message

    def place_order(self, order: LimitOrder):
        trade = self.create_default_message()

        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        trade.setField(fix.ClOrdID(str(order.id)))
        trade.setField(fix.ClientID(str(order.client_id)))

        trade.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))
        trade.setField(fix.Symbol(order.symbol))
        trade.setField(fix.Side(side_to_fix(order.side)))
        trade.setField(fix.OrdType(fix.OrdType_LIMIT))
        trade.setField(fix.OrderQty(order.qty))
        trade.setField(fix.Price(order.price))
        trade.setField(fix.TransactTime())

        fix.Session.sendToTarget(trade, self.sessionID)

    def cancel_order(self):
        print("Cancelling the following order: ")
        # cancel = self.create_default_message()

        # fix.Session.sendToTarget(cancel, self.sessionID)

########################################################################################################################

    def fromApp(self, message, sessionID):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        type = msgType.getValue()

        if type == fix.MsgType_ExecutionReport:
            exec_type = fix.ExecType()
            message.getField(exec_type)

            if exec_type.getValue() == fix.ExecType_ORDER_STATUS:
                self.on_order_status(message)
            elif exec_type.getValue() == fix.ExecType_FILL:
                self.on_fill(message)

        else:
            return fix.UnsupportedMessageType

    def on_order_status(self, message):
        order_id = fix.ClOrdID()
        message.getField(order_id)

        client_id = fix.ClientID()
        message.getField(client_id)

        order_status = fix.OrdStatus()
        message.getField(order_status)

        self.traders[client_id.getValue()].book_keep(
            int(order_id.getValue()),
            fix_to_order_status(order_status.getValue())
        )

    def on_fill(self, message):
        order_id = fix.ClOrdID()
        message.getField(order_id)

        client_id = fix.ClientID()
        message.getField(client_id)

        order_status = fix.OrdStatus()
        message.getField(order_status)

        transaction_qty = fix.LastQty()
        message.getField(transaction_qty)

        transaction_price = fix.LastPx()
        message.getField(transaction_price)

        self.traders[client_id.getValue()].book_keep(
            int(order_id.getValue()),
            fix_to_order_status(order_status.getValue()),
            transaction_qty.getValue(),
            transaction_price.getValue()
        )


########################################################################################################################
