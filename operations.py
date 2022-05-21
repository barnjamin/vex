from models import *


def set_next_price(self, p: Price, BidSide: abi.Bool):
    # Find the key for the next OrderQueue given incoming price
    if BidSide:
        self.BidPrice = p
    else:
        self.AskPrice = p


def price_match(io: "IncomingOrderType"):
    if io.BidSide:
        return io.Price >= OrderBook.AskPrice
    return io.Price <= OrderBook.BidPrice


def handle_incoming_order(io: IncomingOrder):
    if OrderBook.price_match(io.Price):
        return OrderBook.fill_order(io)
    else:
        return OrderBook.add_new_order(io)


def fill_order(self, io: "IncomingOrderType"):
    oq: OrderQueue = self.get_order_queue(io.Price)

    while not io.filled():
        # We reached the end of this  OrderQueue
        if oq.Highest == 0:
            # Check in the next price
            next_price = self.get_next_price(io.Price)
            if next_price != 0:
                # We've got another OrderQueue to check
                self.set_next_price(next_price)
                io.Price = next_price
                return self.handle_incoming_order(io)
            else:
                # Side depleted, we're all out of resting orders, just create a new resting order
                return oq.push(io)

        ro = oq.read(oq.Highest)

        # itxn_fill(Order, Price, Size, Addr)

        oq.push_slot(oq.Highest)
        oq.set("Highest", ro.Lower)
        oq.write(
            oq.Highest,
            {
                "Highest": 0,
            },
        )


def cancel_order(self, co: CancelOrder):

    oq: OrderQueue = self.get_order_queue(co.Price)
    ro: RestingOrder = oq.read(co.Slot)

    oq.push_slot(co.Slot)
    oq.write(
        ro.Higher,
        {
            "Lower": ro.Lower,
        },
    )

    oq.write(ro.Lower, {"Higher": ro.Higher})


def change_volume(self, mos: ModifyOrderSize):
    oq: OrderQueue = self.get_order_queue(mos.Price)
    oq.write(mos.Slot, {"Size": mos.Size})


def push_new_order(self, Price, Size, Address):
    oq: OrderQueue = self.get_order_queue(Price)
    slot: Slot = oq.pop_slot()

    oq.write(oq.Lowest, {"Lower": slot})
    oq.write(
        slot,
        {
            "Higher": self.Lowest,
            "Address": Address,
            "Size": Size,
            "Sequence": self.increment_sequence(),
        },
    )


# Each empty slot in our Order book is listed here
# OpenSlots: abi.DynamicArray[abi.Uint16]
# Virtual field?
# Queue: abi.DynamicArray[RestingOrder]


def write(self, slot: Slot, vals: Dict[str, abi.BaseType]):
    box_key: abi.String = self.box_key(slot)
    # overwrite current values in box
    pass


def read(self, slot: Slot) -> RestingOrder:
    box_key: abi.String = self.box_key(slot)
    pass


def pop_slot(self) -> Slot:
    free: Slot = self.OpenSlots[0]
    self.OpenSlots = self.OpenSlots[1:]
    return free


def push_slot(self, slot: Slot):
    self.OpenSlots.append(slot)
    pass


def set(self, field: str, value: abi.BaseType):
    pass


def push(self, io: "IncomingOrderType") -> Expr:
    return Seq(
        # Pop next slot
        (slot := ScratchVar()).store(self.pop_slot()),
        (box_key := ScratchVar()).store(
            get_price_queue_key(io.Price().get(), slot.load())
        ),
        BoxExtract(
            box_key,
            Int(0),
        ),
    )
