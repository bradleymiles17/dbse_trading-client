from pkg.common.Order import LimitOrder, Side
from traders.Trader import Trader
import random, sys


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
            new_price = random.randint(minprice, limit_order.price)
        elif limit_order.side == Side.ASK:
            new_price = random.randint(limit_order.price, maxprice)
        else:
            sys.exit(0)

        return LimitOrder(limit_order.symbol, limit_order.side, limit_order.qty, new_price)
