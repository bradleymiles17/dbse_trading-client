from .Trader import Trader
from agents.models import NewOrder

# Trader subclass Shaver
# shaves a penny off the best price
# if there is no best price, creates "stub quote" at system max/min
class Trader_Shaver(Trader):

    def getorder(self, time, countdown, lob):
        if len(self.orders) < 1:
            order = None
        else:
            limitprice = self.orders[0].price
            otype = self.orders[0].otype
            if otype == 'Bid':
                if lob['bids']['n'] > 0:
                    quoteprice = lob['bids']['best'] + 1
                    if quoteprice > limitprice:
                        quoteprice = limitprice
                else:
                    quoteprice = lob['bids']['worst']
            else:
                if lob['asks']['n'] > 0:
                    quoteprice = lob['asks']['best'] - 1
                    if quoteprice < limitprice:
                        quoteprice = limitprice
                else:
                    quoteprice = lob['asks']['worst']
            order = NewOrder(self.tid, "APPL", self.orders[0].otype, self.orders[0].qty, quoteprice)
            self.lastquote = order
        return order
