from typing import Callable
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


class IncomingOrder(NamedTuple):
    bid_side: abi.Bool
    price: Price
    size: Size


class RestingOrder(NamedTuple):
    address: abi.Address  # 32
    size: abi.Uint64  # 8
    price: abi.Uint64  # 8
    sequence: abi.Uint64  # 8


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
