class Order:
    def __init__(self, price, seq, size):
        self.price: int = price
        self.size: int = size
        self.seq: int = seq

    @staticmethod
    def from_bytes(b):
        price = int.from_bytes(b[:8], "big")
        seq = int.from_bytes(b[8:16], "big")
        size = int.from_bytes(b[16:], "big")
        return Order(price, seq, size)

    @staticmethod
    def bytesize() -> int:
        return 8 + 8 + 8


class OrderBookSide:
    def __init__(self, side: str):
        self.side = side
        self.order_size = Order.bytesize()
        self.orders: list[Order] = []
        self.volume: dict[int, int] = {}

    def add_order(self, order: Order):
        if order.price not in self.volume:
            self.volume[order.price] = 0
        self.volume[order.price] += order.size
        self.orders.append(order)

    def dom(self):
        items = sorted(self.volume.items())
        return ([i[0] for i in items], [i[1] for i in items])

    @staticmethod
    def from_bytes(side: str, box_bytes: bytes):
        obs = OrderBookSide(side)
        for bidx in range(len(box_bytes) // obs.order_size):
            o = Order.from_bytes(
                box_bytes[bidx * obs.order_size : (bidx + 1) * obs.order_size]
            )
            if o.size == 0:
                break
            obs.add_order(o)

        return obs
