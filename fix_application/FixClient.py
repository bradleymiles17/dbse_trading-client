import sys
import argparse
import quickfix as fix


class FixClient(fix.Application):
    orderID = 0
    execID = 0

    def gen_ord_id(self):
        global orderID
        orderID += 1
        return orderID

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

    def toApp(self, sessionID, message):
        print("Recieved the following message: %s" % message.toString())
        return

    def fromApp(self, message, sessionID):
        print("Got message from server")
        return

    def genOrderID(self):
        self.orderID = self.orderID + 1
        return self.orderID

    def genExecID(self) -> str:
        self.execID = self.execID + 1
        return str(self.execID)

    def create_default_message(self):
        message = fix.Message()
        message.getHeader().setField(fix.BeginString(fix.BeginString_FIXT11))

        return message

    def create_bid(self, qty, price):
        print("Creating the following order: ")
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

        print(trade.toString())
        fix.Session.sendToTarget(trade, self.sessionID)

    def create_ask(self, qty, price):
        print("Creating the following order: ")
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

        print(trade.toString())
        fix.Session.sendToTarget(trade, self.sessionID)

    def cancel_order(self):
        print("Cancelling the following order: ")
        cancel = self.create_default_message()

        fix.Session.sendToTarget(cancel, self.sessionID)


if __name__ == '__main__':
    try:
        settings = fix.SessionSettings("client.cfg")
        application = FixClient()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        while 1:
            input_str = input()
            if input_str == '1':
                print("Create BID")
                application.create_bid(10, 100)
            if input_str == '2':
                print("Create ASK")
                application.create_ask(10, 100)
            if input_str == '3':
                print("Create MULTI")
                # qty, price
                application.create_ask(20, 140)
                application.create_ask(10, 150)
                application.create_bid(35, 150)
            if input_str == '4':
                sys.exit(0)
            if input_str == 'd':
                import pdb

                pdb.set_trace()
            else:
                print("Valid input is 1 for order, 2 for exit")
                continue
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
