import random
import sys

from pkg.common.Order import LimitOrder, Side
from traders.Trader import Trader


# Trader subclass ZI-C
# After Gode & Sunder 1993
class TraderZIC(Trader):

    def get_order(self, countdown, lob):
        limit_order = self.sample_limit_order()

        if limit_order is None:
            return None

        minprice = lob['bids']['worst']
        maxprice = lob['asks']['worst']

        if limit_order.side == Side.BID:
            new_price = round(random.uniform(minprice, limit_order.price), 0)
        elif limit_order.side == Side.ASK:
            new_price = round(random.uniform(limit_order.price, maxprice), 0)
        else:
            sys.exit(0)

        return LimitOrder(limit_order.id, limit_order.client_id, limit_order.symbol, limit_order.side, limit_order.qty, new_price)
