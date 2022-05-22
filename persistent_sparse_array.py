from typing import Literal
from pyteal import *
from models import NamedTuple

kb = int(2**10)
MAX_BOX_SIZE = 16 * kb

BOX_MBR = 2500
BOX_BYTES = 400


# General strategy:
#   when num slots is avail is low, include extra page reference
#   in transaction

PageIndicies = abi.StaticArray[abi.Uint8, Literal[32]]



# Pages represents up to N pages of orders,
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

class Doofus:

    def __init__(self, key: str, t: NamedTuple, size: int):
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
            Int(int(MAX_BOX_SIZE/4)),
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