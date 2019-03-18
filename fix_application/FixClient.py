import sys, random

import quickfix as fix

from fix_application.traders.Trader_Giveaway import Trader_Giveaway
from pkg.common.Order import *
from pkg.qf_map import *


class FixClient(fix.Application):
    orderID = 0
    execID = 0

    def genOrderID(self):
        self.orderID = self.orderID + 1
        return str(self.orderID)

    def genExecID(self) -> str:
        self.execID = self.execID + 1
        return str(self.execID)

    def onCreate(self, sessionID):
        return

    def onLogon(self, sessionID):
        self.sessionID = sessionID
        print("Successful Logon to session '%s'." % sessionID.toString())
        return

    def onLogout(self, sessionID): return

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

    def create_bid(self, qty, price):
        trade = self.create_default_message()

        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))  # 39=D
        trade.setField(fix.ClOrdID(self.genExecID()))  # 11=Unique order

        trade.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))  # 21=3 (Manual order, best executiona)
        trade.setField(fix.Symbol('SMBL'))  # 55=SMBL ?
        trade.setField(fix.Side(fix.Side_BUY))  # 43=1 Buy
        trade.setField(fix.OrdType(fix.OrdType_LIMIT))  # 40=2 Limit order
        trade.setField(fix.OrderQty(qty))  # 38=100
        trade.setField(fix.Price(price))
        trade.setField(fix.TransactTime())

        fix.Session.sendToTarget(trade, self.sessionID)


    def create_ask(self, qty, price):
        trade = self.create_default_message()

        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))  # 39=D
        trade.setField(fix.ClOrdID(self.genExecID()))  # 11=Unique order

        trade.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))  # 21=3 (Manual order, best executiona)
        trade.setField(fix.Symbol('SMBL'))  # 55=SMBL ?
        trade.setField(fix.Side(fix.Side_SELL))  # 43=1 Buy
        trade.setField(fix.OrdType(fix.OrdType_LIMIT))  # 40=2 Limit order
        trade.setField(fix.OrderQty(qty))  # 38=100
        trade.setField(fix.Price(price))
        trade.setField(fix.TransactTime())

        fix.Session.sendToTarget(trade, self.sessionID)

    def create_order(self, order: LimitOrder):
        trade = self.create_default_message()

        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))
        trade.setField(fix.ClOrdID(order.ClOrdID))

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
        cancel = self.create_default_message()

        fix.Session.sendToTarget(cancel, self.sessionID)

    ####################################################################################################################

    def fromApp(self, message, sessionID):
        print("Received: %s" % message.toString())

        msgType = fix.MsgType()
        message.getHeader().getField(msgType)
        type = msgType.getValue()

        if type == fix.MsgType_ExecutionReport:
            self.on_execution_report(message)
        else:
            return fix.UnsupportedMessageType

    def on_execution_report(self, message):
        for id in traders:
            print("bookeep trader %d" % id)
            # traders[id].bookkeep(message.toString(), "order", True)


####################################################################################################################

traders = {}


def create_random_limit_order():
    return LimitOrder(
        application.genOrderID(),
        "SMBL",
        Side.BID if (random.randint(0, 1) == 0) else Side.ASK,
        round(random.uniform(0.80, 1.50), 2),
        float(random.randint(10, 50))
    )


if __name__ == '__main__':
    try:
        settings = fix.SessionSettings("client.cfg")
        application = FixClient()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        # type, tid, balance
        trader1 = Trader_Giveaway("GVWY", 1, 0.00)
        trader1.add_order(create_random_limit_order())
        trader2 = Trader_Giveaway("GVWY", 2, 0.00)
        trader2.add_order(create_random_limit_order())

        traders[trader1.tid] = trader1
        traders[trader2.tid] = trader2

        while 1:
            input_str = input()
            if input_str == 'b':
                application.create_bid(10, 120)
                application.create_bid(10, 110)
                application.create_bid(10, 150)
            if input_str == 'a':
                application.create_ask(10, 150)
                application.create_ask(10, 170)
                application.create_ask(10, 120)
                application.create_ask(20, 170)
            if input_str == 'r':
                for x in range(1000):
                    application.create_order(create_random_limit_order())
            if input_str == "algo":
                time_left = time.time()

                tid = list(traders.keys())[random.randint(0, len(traders) - 1)]
                order = traders[tid].get_order(time_left, {})

                application.create_order(order)
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
