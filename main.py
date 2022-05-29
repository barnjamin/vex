import base64
import random
from algosdk.v2client import algod
from algosdk.future.transaction import BoxReference, logic
from algosdk.atomic_transaction_composer import AccountTransactionSigner

from sandbox import get_sandbox_accounts
from vex import vex, ask_pq, bid_pq
from application_client import ApplicationClient

host = "http://localhost:4001"
token = "a" * 64

client = ApplicationClient(algod.AlgodClient(token, host), vex)

accts = get_sandbox_accounts()
addr, sk = accts[-1]
signer = AccountTransactionSigner(sk)

boxes = [BoxReference(0, ask_pq.box_name_str), BoxReference(0, bid_pq.box_name_str)]


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

    orders = 500
    app_id = 8104

    mid = 50


    if True:
        app_id, app_addr = client.create(signer, int(4e8))
        print(f"Created {app_id} with app address {app_addr}")

        result = client.bootstrap(signer, [], boxes=boxes)
        print(result)

        for x in range(orders):
            bid = x % 2 == 0
            side = "bid" if bid else "ask"

            start, stop = mid - 10, 100
            if not bid:
                start, stop = 0, mid + 10 

            price, size = random.randint(start, stop), random.randint(1, 10)  * 10
            filled = client.new_order(signer, [bid, price, size], boxes=boxes)
            print("{} Filled {}".format(side, filled))

    ## Start to build off chain representation
    order_size = 24

    bbs = OrderBookSide("bid")
    bb = client.client.application_box_data(app_id, "bid_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(orders):
        o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
        if o.size == 0:
            break

        bbs.add_order(o)

    abs = OrderBookSide("ask")
    bb = client.client.application_box_data(app_id, "ask_book")
    box_bytes = base64.b64decode(bb["value"])
    for bidx in range(orders):
        o = Order.from_bytes(box_bytes[bidx * order_size : (bidx + 1) * order_size])
        if o.size == 0:
            break

        abs.add_order(o)

    import matplotlib.pyplot as plt
    plt.bar(*bbs.dom())
    plt.bar(*abs.dom())
    plt.savefig('dom.png')
