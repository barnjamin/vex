import random
import base64
import algosdk
from beaker import sandbox, client
from beaker.client.api_providers import AlgoNode, Network
from vex import Vex


def demo():
    # TODO: can the App tell us which boxes it wants?
    boxes = [
        (0, Vex.ask_queue._box_name),
        (0, Vex.bid_queue._box_name),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
        (0, ""),
    ]

    # Setup
    # algod_client = sandbox.clients.get_algod_client()
    algod_client = AlgoNode(network=Network.BetaNet).algod()

    signer = sandbox.kmd.get_accounts().pop().signer

    app_client = client.ApplicationClient(algod_client, Vex(), signer=signer)

    app_id, _, _ = app_client.create()
    print(f"CREATED APP ID: {app_id}")
    app_client.fund(int(1e7))
    app_client.call(Vex.boostrap, boxes=boxes)

    # Simulate incoming orders
    orders = 200
    mid = 50
    for x in range(orders):
        bid = x % 2 == 0
        side = "bid" if bid else "ask"

        start, stop = mid - 3, mid + 5
        if bid:
            start, stop = mid - 5, mid + 3

        price, size = random.randint(start, stop), random.randint(1, 10) * 10
        result = app_client.call(
            Vex.new_order, is_bid=bid, price=price, size=size, boxes=boxes
        )
        print("{} Filled {}".format(side, result.return_value))

    return app_id


def chart_dom(app_id: int, algod_client: algosdk.v2client.algod.AlgodClient):
    import matplotlib.pyplot as plt

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


if __name__ == "__main__":
    app_id = demo()
    chart_dom(app_id, AlgoNode(Network.BetaNet).algod())
