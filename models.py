from typing import Callable, cast, List
from pyteal import *


class NamedTuple(abi.Tuple):
    def __init__(self):
        self.type_specs = {
            k: cast(abi.BaseType, v()).type_spec()
            for k, v in self.__annotations__.items()
        }
        self.field_names = list(self.type_specs.keys())

        for idx in range(len(self.field_names)):
            name = self.field_names[idx]
            setattr(self, name, self.getter(idx))

        super().__init__(abi.TupleTypeSpec(*self.type_specs.values()))

    def put(self, *exprs: Expr)->Expr:

        abi_types: List[abi.BaseType] = []
        setters: List[Expr] = []

        for idx, expr in enumerate(exprs):
            tspec = self.type_specs[self.field_names[idx]]
            #print(tspec.storage_type())
            #print(expr.type_of())
            #if expr.type_of() != tspec.storage_type():
            #    raise TealTypeError(tspec.storage_type(), expr.type_of()) 

            val: abi.BaseType = tspec.new_instance()
            setters.append(val.set(expr))
            abi_types.append(val)

        return Seq(
            *setters,
            self.set(*abi_types)
        )
            

    def get_type(self):
        return self.type_spec().annotation_type()

    def getter(self, idx) -> Callable:
        return lambda: self.__getitem__(idx)

    def __str__(self) -> str:
        return super().type_spec().__str__()


class VexAccount(NamedTuple):
    address: abi.Address
    balance_a: abi.Uint64
    balance_b: abi.Uint64
    reserved_a: abi.Uint64
    reserved_b: abi.Uint64
    credits: abi.Uint64


class RestingOrder(NamedTuple):
    price: abi.Uint64
    sequence: abi.Uint64
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
IncomingOrderCancelType = IncomingOrderCancel().get_type()
IncomingOrderChangeSizeType = IncomingOrderChangeSize().get_type()
