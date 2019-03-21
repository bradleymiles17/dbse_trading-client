import sys, time, random

from fix_application import FixClient
from pkg.common.Order import Order


# Trader superclass
# all Traders have a trader id, bank balance, blotter, and list of orders to execute
class Trader:

    def __init__(self, t_type: str, tid: str, balance: float, fix_client: FixClient):
        self.t_type = t_type  # what type / strategy this trader is
        self.tid = tid  # trader unique ID code
        self.birthtime = time.time()  # used when calculating age of a trader/strategy

        # LIVE DATA
        self.balance = balance  # money in the bank
        self.blotter = []  # record of trades executed
        self.orders = {}  # customer orders currently being worked (fixed at 1)
        self.n_quotes = 0  # number of quotes live on LOB
        # self.willing = 1  # used in ZIP etc
        # self.able = 1  # used in ZIP etc

        # HISTORY
        self.profitpertime = 0  # profit per unit time
        self.n_trades = 0  # how many trades has this trader done?
        self.lastquote = None  # record of what its last quote was

        self.fix_client = fix_client


    def __str__(self):
        return '[TID %s type %s balance %s blotter %s orders %s n_trades %s profitpertime %s]' \
               % (self.tid, self.t_type, self.balance, self.blotter, self.orders, self.n_trades, self.profitpertime)

    def add_order(self, order: Order):
        print(self.tid + " ADD " + str(order))
        self.orders[order.ClOrdID] = order
        return True

    def del_order(self, order: Order):
        print(self.tid + " DEL " + str(order))
        del self.orders[order.ClOrdID]

    def sample_order(self):
        return random.choice(list(self.orders.items()))

    def bookkeep(self, trade, order, verbose):

        outstr = ""
        for order in self.orders: outstr = outstr + str(order)

        self.blotter.append(trade)  # add trade record to trader's blotter
        # NB What follows is **LAZY** -- assumes all orders are quantity=1
        transactionprice = trade['price']
        if self.orders[0].is_buy:
            profit = self.orders[0].price - transactionprice
        else:
            profit = transactionprice - self.orders[0].price
        self.balance += profit
        self.n_trades += 1
        # self.profitpertime = self.balance / (time - self.birthtime)

        if profit < 0:
            print(profit)
            print(trade)
            print(order)
            sys.exit()

        if verbose: print('%s profit=%d balance=%d profit/time=%d' % (outstr, profit, self.balance, self.profitpertime))
        self.del_order(order)  # delete the order

    # specify how trader responds to events in the market
    # this is a null action, expect it to be overloaded by specific algos
    def respond(self, time, lob, trade, verbose):
        return None

    # specify how trader mutates its parameter values
    # this is a null action, expect it to be overloaded by specific algos
    def mutate(self, time, lob, trade, verbose):
        return None
