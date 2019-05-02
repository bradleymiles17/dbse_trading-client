import random
import time

from fix_engine import FixClient
from pkg.common.Order import Order, Side, OrderState
from pkg.common.Trade import Trade


# Trader superclass
# all Traders have a trader id, bank balance, blotter, and list of orders to execute


class Trader:

    def __init__(self, t_type: str, tid: str, balance: float, verbose, fix_client: FixClient):
        self.t_type = t_type  # what type / strategy this trader is
        self.tid = tid  # trader unique ID code
        self.birthtime = time.time()  # used when calculating age of a trader/strategy
        self.limit_orders = {}

        # LIVE DATA
        self.balance = balance  # money in the bank
        self.blotter = []  # record of trades executed
        self.orders = {}  # customer orders currently being worked (fixed at 1)
        self.n_quotes = 0 # number of quotes able to trade

        # HISTORY
        self.profitpertime = 0  # profit per unit time
        self.n_trades = 0  # how many trades has this trader done?
        self.last_quote = None  # record of what its last quote was

        self.fix_client = fix_client
        self.verbose = verbose


    def __str__(self):
        return '[TID %s type %s balance %s blotter %s orders %s n_trades %s profitpertime %s]' \
               % (self.tid, self.t_type, self.balance, self.blotter, self.orders, self.n_trades, self.profitpertime)

    def add_limit_order(self, order: Order):
        if self.verbose:
            print(self.tid + " new " + str(order))
        self.limit_orders[order.id] = order
        self.n_quotes = len(self.limit_orders)
        return True

    def sample_limit_order(self):
        ids = list(self.limit_orders.keys() - self.orders.keys())
        if len(ids) < 1:
            return None

        return self.limit_orders[random.choice(ids)]

    def place_order(self, order: Order):
        self.orders[order.id] = order
        self.fix_client.place_order(order)

    def cancel_all_live(self):
        keys = list(self.orders)
        for index in keys:
            self.fix_client.cancel_order(self.orders[index])

        self.orders = {}
        self.limit_orders = {}

    def book_keep(self, order_id: int, status: OrderState, trade: Trade = None):
        order = self.orders[order_id]
        order.order_state = status

        # TRADE OCCURRED
        if trade is not None:
            limit = self.limit_orders[order_id]

            if order.side == Side.BID:
                profit = (limit.price - trade.price) * trade.qty
            else:
                profit = (trade.price - limit.price) * trade.qty

            self.balance += profit
            self.n_trades += 1
            self.blotter.append(trade)
            self.profitpertime = self.balance / (time.time() - self.birthtime)

            order.remaining -= trade.qty

        if self.verbose:
            print('%s %s %s' % (self.tid, status, order))

        if order.remaining == 0:
            del self.limit_orders[order_id]
            del self.orders[order_id]
            self.n_quotes = len(self.limit_orders)
        else:
            self.orders[order_id] = order

    # returns the next order the agent wants on the exchange
    def get_order(self, countdown, lob):
        return None

    # specify how trader responds to events in the market
    # this is a null action, expect it to be overloaded by specific algos
    def respond(self, time, lob, trade, verbose):
        return None

    # specify how trader mutates its parameter values
    # this is a null action, expect it to be overloaded by specific algos
    def mutate(self, time, lob, trade, verbose):
        return None
