from django.db import models
from typing import Optional


# # Create your models here.

class NewOrder:
    def __init__(self, trader_id, symbol, is_buy, qty, price: Optional[float]):
        self.trader_id = trader_id
        self.symbol = symbol
        self.is_buy = is_buy
        self.qty = qty
        self.price = price

    def __str__(self):
        return '[TID:%s %s %s Q=%s P=%.2f]' % \
               (self.trader_id, self.symbol, "BID" if self.is_buy else "ASK", self.qty, self.price)

    def toJSON(self):
        return {
            "trader_id": self.trader_id,
            "symbol": self.symbol,
            "is_buy": self.is_buy,
            "qty": self.qty,
            "price": self.price
        }
