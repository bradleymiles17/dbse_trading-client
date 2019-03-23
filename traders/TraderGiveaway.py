from pkg.common.Order import LimitOrder
from traders.Trader import Trader


# Trader subclass Giveaway
# even dumber than a ZI-U: just give the deal away
# (but never makes a loss)
class TraderGiveaway(Trader):

    def get_order(self, countdown, lob):
        limit_order = self.sample_limit_order()

        if limit_order is None:
            return None

        order = LimitOrder(limit_order.id, limit_order.client_id, limit_order.symbol, limit_order.side, limit_order.qty, limit_order.price)
        return order
