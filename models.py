from typing import Any, Dict, Callable, Literal, Union, List
from pyteal import *

kb = int(2**10)
MAX_BOX_SIZE = 16 * kb

BOX_MBR = 2500
BOX_BYTES = 400

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
    address: abi.Address
    size: Size
    sequence: Sequence
    higher: Slot
    lower: Slot


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


class GlobalStorageValue:

    key: str
    t: abi.BaseType
    immutable: bool

    def __init__(self, key: str, t: abi.BaseType, immutable=False):
        self.key = Bytes(key)
        self.t = t
        self.immutable = immutable  # TODO make final

    def set_default(self) -> Expr:
        stack_type = self.t.type_spec().storage_type()
        if stack_type == TealType.uint64:
            return App.globalPut(self.key, Itob(Int(0)))
        else:
            return App.globalPut(self.key, Bytes(""))

    def set(self, val: abi.BaseType) -> Expr:
        if isinstance(abi.BaseType, val):
            return App.globalPut(self.key, val.encode())
        else:
            return App.globalPut(self.key, val.encode())

    def get(self) -> Expr:
        return App.globalGet(self.key)

    def getElse(self, val: Expr) -> Expr:
        return Seq(
            v := App.globalGetEx(Int(0), self.key), If(v.hasValue(), v.value(), val)
        )


class LocalStorageValue:
    def __init__(self, key: str, t: abi.BaseType):
        self.key = key
        self.t = t

    def set(self, acct: abi.Account, val: Union[abi.BaseType, Bytes]) -> Expr:
        if isinstance(abi.BaseType, val):
            return App.localPut(self.key, acct.encode(), val.encode())
        else:
            return App.localPut(self.key, acct.encode(), val.encode())

    def get(self, acct: abi.Account) -> Expr:
        return self.t.decode(App.localGet(self.key, acct.encode()))

    def getElse(self, acct: abi.Address, val: Expr) -> Expr:
        return self.t.decode(
            Seq(
                v := App.localGetEx(Int(0), acct.encode(), self.key),
                If(v.hasValue(), v.value(), val),
            )
        )


class AppState:
    Global: Dict[str, GlobalStorageValue]
    Local: Dict[str, LocalStorageValue]

    def init_globals(self):
        return Seq(*[v.set_default() for v in self.Global.values()])


# General strategy:
#   when num slots is avail is low, include extra page reference
#   in transaction

PageIndicies = abi.StaticArray[abi.Uint8, Literal[32]]


class Doofus:
    # Pages represents up to 10 pages of orders,
    # each page has an address (32 byte array)
    # each index for each page has an associated bit
    # in the Address byte array
    # is stored at a uint8 index per page

    # box key prefix
    # track slots open
    # if no slots open,
    # manage adding pages, (need txn to include it)
    # todo: figure out who to charge?
    # assign slot to write
    # ABI r/w codec
    # static ABI Type _only_, so we can track offsets

    def __init__(self, key: str, t: "NamedTuple"):
        self.key = key
        self.t = t
        self.encoded_size = abi.sizeof(t.get_type())
        self.pages = abi.make(abi.DynamicArray[PageIndicies])

    def initialize(self) -> Expr:
        return BoxCreate(Bytes(f"{self.key}-pages"), Int(MAX_BOX_SIZE))

    def dealloc(self, page: Expr) -> Expr:
        return BoxDelete(self.page_name(page))

    def get_page_indicies(self) -> Expr:
        return BoxExtract(
            Bytes(f"{self.key}-pages"),
            Int(0),
            Int(32 * 10),
        )

    def write_page_indicies(self, page: Expr) -> Expr:
        return BoxReplace(Bytes(f"{self.key}-pages"), Int(0), page)

    def page_name(self, page: Expr) -> Expr:
        return Concat(Bytes(self.key), page)

    def alloc(self) -> Expr:
        return Seq(
            self.pages.decode(self.get_page_indicies()),
            BoxCreate(
                self.page_name(Suffix(Itob(self.pages.length()), Int(7))),
                Int(MAX_BOX_SIZE),
            ),
        )

    def reserve_slot(self) -> Expr:
        return Seq(
            (index := ScratchVar()).store(Int(0)),
            (page := ScratchVar()).store(Int(0)),
            self.pages.decode(self.get_page_indicies()),
            For(
                page.store(Int(0)),
                page.load() < self.pages.length(),
                page.store(page.load() + Int(1)),
            ).Do(
                Seq(
                    # Get next Index
                    (pi := abi.make(PageIndicies)).set(self.pages[page.load()]),
                    index.store(BitLen(pi.encode())),
                    # Set slot to occupied
                    self.write_page_indicies(
                        SetBit(
                            self.pages.encode(),
                            (page.load() * Int(256)) + index.load(),
                            Int(0),
                        )
                    ),
                )
            ),
            # If we need to allocate a new page, do it
            If(
                And(page.load() == Int(0), index.load() == Int(0)),
                Seq(
                    self.alloc(),
                    page.store(self.pages.length()),
                )
            ),
            Concat(
                Suffix(Itob(page.load()), Int(7)), 
                Suffix(Itob(index.load()), Int(7))
            ),
        )

    def write(self, slot: abi.Uint16, t: "NamedTuple") -> Expr:
        return Seq(
            (page := abi.Uint8()).decode(Extract(slot.encode(), Int(0), Int(1))),
            (idx := abi.Uint8()).decode(Extract(slot.encode(), Int(1), Int(1))),
            BoxReplace(
                self.page_name(page.encode()),
                Int(self.encoded_size) * idx.get(),
                t.encode(),
            ),
        )

    def read(self, slot: abi.Uint16)->Expr:
        return Seq(
            (page := abi.Uint8()).decode(Extract(slot.encode(), Int(0), Int(1))),
            (idx := abi.Uint8()).decode(Extract(slot.encode(), Int(1), Int(1))),
            BoxExtract(
                self.page_name(page.encode()),
                Int(self.encoded_size) * idx.get(),
                Int(self.encoded_size) * (idx.get()+Int(1))
            ),
        )
