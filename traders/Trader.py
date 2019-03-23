import sys, time, random

from fix_application import FixClient
from pkg.common.Order import Order, Side, OrderState

# Trader superclass
# all Traders have a trader id, bank balance, blotter, and list of orders to execute
from pkg.common.Trade import Trade


class Trader:

    def __init__(self, t_type: str, tid: str, balance: float, fix_client: FixClient):
        self.t_type = t_type  # what type / strategy this trader is
        self.tid = tid  # trader unique ID code
        self.birthtime = time.time()  # used when calculating age of a trader/strategy
        self.limit_orders = {}

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
        self.last_quote = None  # record of what its last quote was

        self.fix_client = fix_client


    def __str__(self):
        return '[TID %s type %s balance %s blotter %s orders %s n_trades %s profitpertime %s]' \
               % (self.tid, self.t_type, self.balance, self.blotter, self.orders, self.n_trades, self.profitpertime)

    def add_limit_order(self, order: Order):
        print(self.tid + " add " + str(order))
        self.limit_orders[order.id] = order
        return True

    def sample_limit_order(self):
        ids = list(self.limit_orders.keys() - self.orders.keys())
        if len(ids) < 1:
            return None

        return self.limit_orders[random.choice(ids)]

    def place_order(self, order: Order):
        print("%s place %s" % (self.tid, order))
        self.orders[order.id] = order
        self.fix_client.place_order(order)
        return True

    def book_keep(self, order_id: int, status: OrderState, trade_qty: float = None, trade_price: float = None):
        order = self.orders[order_id]
        order.order_state = status
        # self.blotter.append(trade)  # add trade record to trader's blotter
        # NB What follows is **LAZY** -- assumes all orders are quantity=1
        # transactionprice = trade['price']

        # TRADE OCCURRED
        if trade_qty is not None and trade_price is not None:
            if order.side == Side.BID:
                profit = (order.price - trade_price) * trade_qty
            else:
                profit = (trade_price - order.price) * trade_qty

            self.balance += profit
            self.n_trades += 1
            self.profitpertime = self.balance / (time.time() - self.birthtime)

            order.remaining -= trade_qty

        print('%s %s %s' % (self.tid, status, order))
        print('%s N=%d B=%.2f' % (self.tid, self.n_trades, self.balance))

        if order.remaining == 0:
            del self.limit_orders[order_id]
            del self.orders[order_id]
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
