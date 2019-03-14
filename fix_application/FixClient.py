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

    def put_order(self):
        print("Creating the following order: ")
        trade = fix.Message()
        trade.getHeader().setField(fix.BeginString(fix.BeginString_FIXT11))  #
        trade.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))  # 39=D
        trade.setField(fix.ClOrdID(self.genExecID()))  # 11=Unique order

        trade.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))  # 21=3 (Manual order, best executiona)
        trade.setField(fix.Symbol('SMBL'))  # 55=SMBL ?
        trade.setField(fix.Side(fix.Side_BUY))  # 43=1 Buy
        trade.setField(fix.OrdType(fix.OrdType_LIMIT))  # 40=2 Limit order
        trade.setField(fix.OrderQty(100))  # 38=100
        trade.setField(fix.Price(10))
        trade.setField(fix.TransactTime())
        print(trade.toString())
        fix.Session.sendToTarget(trade, self.sessionID)


def initialise_fix_app(config_file):
    try:
        settings = fix.SessionSettings(config_file)
        application = FixClient()
        storeFactory = fix.FileStoreFactory(settings)
        logFactory = fix.FileLogFactory(settings)
        initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)
        initiator.start()

        return application
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(e)
