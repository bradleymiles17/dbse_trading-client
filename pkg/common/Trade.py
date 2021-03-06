
id = 0


def gen_trade_id():
    global id
    id = id + 1
    return id


class Trade:
    def __init__(self, order_id: int, client_id: int, qty, price):
        self.id = gen_trade_id()
        self.order_id = order_id
        self.client_id = client_id
        self.qty = qty
        self.price = price


    def __str__(self):
        return 'TRADE: [Q=%s P=%.2f]' % \
               (self.qty, self.price)
