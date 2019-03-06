from .Trader import Trader
from agents.models import NewOrder


# Trader subclass Giveaway
# even dumber than a ZI-U: just give the deal away
# (but never makes a loss)
class Trader_Giveaway(Trader):

    def get_order(self, countdown, lob):
        if len(self.orders) < 1:
            order = None
        else:
            quoteprice = self.orders[0].price
            order = NewOrder(self.tid, "BAM", self.orders[0].otype, self.orders[0].qty, quoteprice)
            self.lastquote = order
        return order
