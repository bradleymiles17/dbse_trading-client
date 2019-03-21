import sys, random, argparse, math

import quickfix as fix

from pkg.common.Order import *
from pkg.qf_map import *


class FixClient(fix.Application):

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
        print("Sending message: %s" % message.toString())
        return

    def create_default_message(self):
        message = fix.Message()
        message.getHeader().setField(fix.BeginString(fix.BeginString_FIXT11))

        return message

    def place_order(self, order: LimitOrder):
        trade = self.create_default_message()

        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        trade.setField(fix.ClOrdID(str(order.id)))

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
            self.on_execution_report(message)
        else:
            return fix.UnsupportedMessageType

    def on_execution_report(self, message):
        print("Received: %s" % message.toString())

        # for id in traders:
        # traders[id].bookkeep(message.toString(), "order", True)


########################################################################################################################
