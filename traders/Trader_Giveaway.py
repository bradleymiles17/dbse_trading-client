from pkg.common.Order import LimitOrder
from traders.Trader import Trader


# Trader subclass Giveaway
# even dumber than a ZI-U: just give the deal away
# (but never makes a loss)
class Trader_Giveaway(Trader):

    def get_order(self, countdown, lob):
        if len(self.orders) < 1:
            order = None
        else:
            id, quote = self.sample_order()

            order = LimitOrder("SMBL", quote.side, quote.qty, quote.price)
            self.lastquote = order
        return order
