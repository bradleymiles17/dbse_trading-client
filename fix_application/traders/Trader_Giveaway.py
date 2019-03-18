from pkg.common.Order import LimitOrder
from .Trader import Trader


# Trader subclass Giveaway
# even dumber than a ZI-U: just give the deal away
# (but never makes a loss)
class Trader_Giveaway(Trader):

    def get_order(self, countdown, lob):
        if len(self.orders) < 1:
            order = None
        else:
            current_quote = self.orders[0]
            quoteprice = current_quote.price
            order = LimitOrder(self.tid, "SMBL", current_quote.side, current_quote.qty, quoteprice)
            self.lastquote = order
        return order
