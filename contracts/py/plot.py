import algosdk
import base64
import matplotlib.pyplot as plt # type: ignore

def chart_dom(app_id: int, algod_client: algosdk.v2client.algod.AlgodClient):

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

    # Start to build off chain representation
    order_size = 24
    bbs = OrderBookSide("bid")
    bb = algod_client.application_box_by_name(app_id, b"bid_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(len(box_bytes) // order_size):
        o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
        if o.size == 0:
            break

        bbs.add_order(o)

    abs = OrderBookSide("ask")
    bb = algod_client.application_box_by_name(app_id, b"ask_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(len(box_bytes) // order_size):
        o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
        if o.size == 0:
            break

        abs.add_order(o)

    plt.bar(*bbs.dom())
    plt.bar(*abs.dom())
    plt.savefig("dom.png")
