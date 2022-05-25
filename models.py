from typing import  Callable
from pyteal import *

# First byte is which page
# Second byte is index into that page
Slot = abi.Uint16
Page = abi.Uint8
Idx = abi.Uint8

Price = abi.Uint64
Size = abi.Uint64
Sequence = abi.Uint64


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


class OrderBook(NamedTuple):
    """ """

    mid_price: Price
    ask_price: Price
    bid_price: Price
    decimals: abi.Uint8
    sequence: abi.Uint64


class OrderQueue(NamedTuple):
    """
    OrderQueue Holds pointers to both sides of the
    order book queue for a given price
    """

    # Pointer to first element in Queue
    # Used to find first order to fill
    head: Slot

    # Pointer to last element in queue
    # Used to append new orders
    tail: Slot

    num_pages: abi.Uint64


class IncomingOrder(NamedTuple):
    bid_side: abi.Bool
    price: Price
    size: Size


class RestingOrder(NamedTuple):
    address: abi.Address # 32
    size: abi.Uint64     # 8 
    price: abi.Uint64    # 8
    sequence: abi.Uint64 # 8
                         # 56


class CancelOrder(NamedTuple):
    price: Price
    address: abi.Address
    slot: Slot


class ModifyOrderSize(NamedTuple):
    price: Price
    address: abi.Address
    slot: Slot
    current_size: Size
    new_size: Size


IncomingOrderType = IncomingOrder().get_type()
OrderBookType = OrderBook().get_type()
OrderQueueType = OrderQueue().get_type()
RestingOrderType = RestingOrder().get_type()
ModifyOrderSizeType = ModifyOrderSize().get_type()
CancelOrderType = CancelOrder().get_type()