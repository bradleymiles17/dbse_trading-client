from pkg.common.Order import Side, LimitOrder
from traders.Trader import Trader


# Trader subclass Shaver
# shaves a penny off the best price
# if there is no best price, creates "stub quote" at system max/min
class TraderShaver(Trader):

    def get_order(self, countdown, lob):
        limit_order = self.sample_limit_order()

        if limit_order is None:
            return None

        if limit_order.side == Side.BID:
            if lob['bids']['qty'] > 0:
                quote_price = lob['bids']['best'] + 1
                new_price = min(quote_price, limit_order.price)
            else:
                new_price = lob['bids']['worst']
        else:
            if lob['asks']['qty'] > 0:
                quote_price = lob['asks']['best'] - 1
                new_price = max(quote_price, limit_order.price)
            else:
                new_price = lob['asks']['worst']

        return LimitOrder(
            limit_order.id,
            limit_order.client_id,
            limit_order.symbol,
            limit_order.side,
            limit_order.qty,
            new_price
        )
