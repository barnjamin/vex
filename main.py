import random
import base64

from beaker import sandbox, client
from vex import Vex


class Order:
    def __init__(self, price, seq, size):
        self.price = price
        self.size = size
        self.seq = seq

    @staticmethod
    def from_bytes(b):
        price = int.from_bytes(b[:8], "big")
        seq = int.from_bytes(b[8:16], "big")
        size = int.from_bytes(b[16:], "big")
        return Order(price, seq, size)


class OrderBookSide:
    def __init__(self, side):
        self.side = side
        self.orders = []
        self.volume = {}

    def add_order(self, order: Order):
        if order.price not in self.volume:
            self.volume[order.price] = 0
        self.volume[order.price] += order.size
        self.orders.append(order)

    def dom(self):
        items = sorted(self.volume.items())
        return ([i[0] for i in items], [i[1] for i in items])


if __name__ == "__main__":


    # TODO: can the App tell us which boxes it wants?
    boxes = [(0, Vex.ask_pq.box_name_str), (0, Vex.bid_pq.box_name_str)]

    algod_client = sandbox.clients.get_algod_client()
    signer = sandbox.kmd.get_accounts().pop().signer

    app_client = client.ApplicationClient(algod_client, Vex(), signer=signer)

    app_id, app_addr, txid = app_client.create()

    app_client.fund(int(1e7))

    app_client.call(Vex.boostrap, boxes=boxes)

    orders = 50
    mid = 50
    for x in range(orders):
        bid = x % 2 == 0
        side = "bid" if bid else "ask"

        start, stop = mid - 3, mid + 5
        if not bid:
            start, stop = mid - 5, mid + 3

        price, size = random.randint(start, stop), random.randint(1, 10) * 10
        result = app_client.call(
            Vex.new_order, is_bid=bid, price=price, size=size, boxes=boxes
        )
        print([base64.b64decode(l).decode('utf-8') for l in result.tx_info['logs'][:-1]])
        print("{} Filled {}".format(side, result.return_value))

    # Start to build off chain representation
    order_size = 24

    bbs = OrderBookSide("bid")
    bb = app_client.client.application_box_by_name(app_id, b"bid_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(orders):
       o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
       if o.size == 0:
           break

       bbs.add_order(o)

    abs = OrderBookSide("ask")
    bb = app_client.client.application_box_by_name(app_id, b"ask_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(orders):
       o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
       if o.size == 0:
           break

       abs.add_order(o)

    import matplotlib.pyplot as plt

    plt.bar(*bbs.dom())
    plt.bar(*abs.dom())
    plt.savefig("dom.png")
