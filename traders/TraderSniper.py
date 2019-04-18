from pkg.common.Order import LimitOrder, Side
from traders.Trader import Trader


# Trader subclass Sniper
# Based on Shaver,
# "lurks" until time remaining < threshold% of the trading session
# then gets increasing aggressive, increasing "shave thickness" as time runs out
class TraderSniper(Trader):

    def get_order(self, countdown, lob):
        lurk_threshold = 0.2
        shavegrowthrate = 3
        shave = int(1.0 / (0.01 + countdown / (shavegrowthrate * lurk_threshold)))

        limit_order = self.sample_limit_order()

        if limit_order is None or (countdown > lurk_threshold):
            return None

        if limit_order.side == Side.BID:
            if lob['bids']['qty'] > 0:
                quote_price = lob['bids']['best'] + shave
                new_price = min(quote_price, limit_order.price)
            else:
                new_price = lob['bids']['worst']
        else:
            if lob['asks']['qty'] > 0:
                quote_price = lob['asks']['best'] - shave
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
