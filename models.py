from typing import Callable
from xmlrpc.client import Boolean
from pyteal import *


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


# TODO: add address
class RestingOrder(NamedTuple):
    price: abi.Uint64
    sequence: abi.Uint64
    size: abi.Uint64


class IncomingOrder(NamedTuple):
    bid_side: abi.Bool
    price: abi.Uint64
    size: abi.Uint64


class IncomingOrderCancel(NamedTuple):
    price: abi.Uint64
    address: abi.Address


class IncomingOrderChangeSize(NamedTuple):
    price: abi.Uint64
    address: abi.Address
    current_size: abi.Uint64
    new_size: abi.Uint64


RestingOrderType = RestingOrder().get_type()
IncomingOrderType = IncomingOrder().get_type()
IncomingOrderCancelType = IncomingOrderCancel().get_type()
IncomingOrderChangeSizeType = IncomingOrderChangeSize().get_type()
