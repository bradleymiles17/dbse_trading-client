import sys, random, argparse

import quickfix as fix

from fix_application.traders.Trader_Giveaway import Trader_Giveaway
from pkg.common.Order import *
from pkg.qf_map import *


class FixClient(fix.Application):

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
        cancel = self.create_default_message()

        fix.Session.sendToTarget(cancel, self.sessionID)

    ####################################################################################################################

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


####################################################################################################################

traders = {}


def create_limit_order(side=None, qty=None, price=None):
    if side is None:
        side = Side.BID if (random.randint(0, 1) == 0) else Side.ASK

    if qty is None:
        qty = float(random.randint(10, 50))

    if price is None:
        price = round(random.uniform(0.80, 1.50), 2)

    return LimitOrder("SMBL", side, qty, price)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FIX Server')
    parser.add_argument('file_name', type=str, help='Name of configuration file')
    args = parser.parse_args()

    try:
        settings = fix.SessionSettings(args.file_name)
        application = FixClient()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        # type, tid, balance
        trader1 = Trader_Giveaway("GVWY", 1, 0.00)
        # trader1.add_order(create_limit_order())
        trader2 = Trader_Giveaway("GVWY", 2, 0.00)
        # trader2.add_order(create_limit_order())

        traders[trader1.tid] = trader1
        traders[trader2.tid] = trader2

        while 1:
            input_str = input()
            if input_str == 'b':
                application.place_order(create_limit_order(Side.BID, 10, 1.20))
                application.place_order(create_limit_order(Side.BID, 10, 1.10))
                application.place_order(create_limit_order(Side.BID, 10, 1.50))
            if input_str == 'b_all':
                application.place_order(create_limit_order(Side.BID, 2000, 2.00))
            if input_str == 'a':
                application.place_order(create_limit_order(Side.ASK, 10, 1.50))
                application.place_order(create_limit_order(Side.ASK, 10, 1.70))
                application.place_order(create_limit_order(Side.ASK, 10, 1.20))
                application.place_order(create_limit_order(Side.ASK, 10, 1.70))
            if input_str == 'r':
                # time + seconds
                t_end = time.time() + 30
                while time.time() < t_end:
                    application.place_order(create_limit_order())
                    time.sleep(0.01)
            if input_str == "algo":
                time_left = time.time()

                tid = list(traders.keys())[random.randint(0, len(traders) - 1)]
                order = traders[tid].get_order(time_left, {})

                application.place_order(order)
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
