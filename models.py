from typing import Dict, Callable
from pyteal import *


Slot = abi.Uint16
Price = abi.Uint64
Size = abi.Uint64
Sequence = abi.Uint64

key_ob_mid = Bytes("obm")
key_ob_bid = Bytes("obb")
key_ob_ask = Bytes("oba")
key_ob_dec = Bytes("obd")

def get_price_queue_key(price: Price, slot: Slot) -> str:
    # given slot, figure out which box and what offset into box
    order_size = 40
    box_size = 16000
    box_index = (slot * order_size) / box_size
    return f"{Price}-{box_index}"


@Subroutine(TealType.none)
def init_orderbook() -> Expr:
    return Seq(
        App.globalPut(key_ob_mid, Int(0)),
        App.globalPut(key_ob_bid, Int(0)),
        App.globalPut(key_ob_ask, Int(0)),
        App.globalPut(key_ob_dec, Int(4))
    )

@Subroutine(TealType.bytes)
def read_orderbook() -> Expr:
    return Seq(
        (mid := Price()).set(App.globalGet(key_ob_mid)),
        (bid := Price()).set(App.globalGet(key_ob_bid)),
        (ask := Price()).set(App.globalGet(key_ob_ask)),
        (decimals := abi.Uint8()).set(App.globalGet(key_ob_dec)),
        (ob:=OrderBook()).set(
            mid, ask, bid, decimals
        ),
        ob.encode()
    )


class NamedTuple(abi.Tuple):
    def __init__(self):
        self.type_specs = {k: v().type_spec() for k, v in self.__annotations__.items()}
        self.field_names = list(self.type_specs.keys())

        for idx in range(len(self.field_names)):
            name = self.field_names[idx]
            setattr(self, name, self.getter(idx))

        super().__init__(abi.TupleTypeSpec(*self.type_specs.values()))

    def get_type(self):
        return self.type_spec().annotation_type()

    def getter(self, idx) -> Callable:
        return lambda: self.__getitem__(idx)

    def __str__(self) -> str:
        return super().type_spec().__str__()


class IncomingOrder(NamedTuple):
    BidSide: abi.Bool
    Price: Price
    Size: Size
    Address: abi.Address

    def filled(self) -> abi.Bool:
        return self.Size == 0


class RestingOrder(NamedTuple):
    Address: abi.Address
    Size: Size
    Sequence: Sequence
    Higher: Slot
    Lower: Slot


class CancelOrder(NamedTuple):
    Price: Price
    Address: abi.Address
    Slot: Slot


class ModifyOrderSize(NamedTuple):
    Price: Price
    Address: abi.Address
    Slot: Slot
    CurrentSize: Size
    NewSize: Size


class OrderBook(NamedTuple):
    Midprice: Price
    AskPrice: Price
    BidPrice: Price
    Decimals: abi.Uint8

    def key() -> str:
        return "ob"

    def get_price_order_queue(self, p: Price) -> "OrderQueue":
        pass

    def get_next_price(self, p: Price, BidSide: abi.Bool) -> "Price":
        # Find the key for the next OrderQueue given incoming price
        pass

    def set_next_price(self, p: Price, BidSide: abi.Bool):
        # Find the key for the next OrderQueue given incoming price
        if BidSide:
            self.BidPrice = p
        else:
            self.AskPrice = p

    def price_match(self, io: IncomingOrder):
        if io.BidSide:
            return io.Price >= self.AskPrice
        return io.Price <= self.BidPrice

    def handle_incoming_order(self, io: IncomingOrder):
        if self.price_match(io.Price):
            self.fill_order(io)
        else:
            self.add_new_order(io)

    def add_new_order(self, io: IncomingOrder):
        oq: OrderQueue = self.get_price_order_queue(io.Price)
        oq.push(io)

    def fill_order(self, io: IncomingOrder):
        oq: OrderQueue = self.get_price_order_queue(io.Price)

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

        oq: OrderQueue = self.get_price_order_queue(co.Price)
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
        oq: OrderQueue = self.get_price_order_queue(mos.Price)
        oq.write(mos.Slot, {"Size": mos.Size})

    def push_new_order(self, Price, Size, Address):
        oq: OrderQueue = self.get_price_order_queue(Price)
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


class OrderQueue:
    MinSize: abi.Uint64
    # Each empty slot in our Order book is listed here
    OpenSlots: abi.DynamicArray[abi.Uint16]
    # Current priority sequence value
    Sequence: abi.Uint64
    # How many orders are resting
    NumOrders: abi.Uint16
    # Top of queue
    Highest: abi.Uint16
    # Bottom of queue
    Lowest: abi.Uint16
    # Mid of queue for faster searches?
    Mid: abi.Uint16
    # Virtual field?
    Queue: abi.DynamicArray[RestingOrder]

    Price: abi.Uint64

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

    def set(field: str, value: abi.BaseType):
        pass

    def push(io: IncomingOrder):
        pass
