from typing import Literal
from pyteal import *
from models import NamedTuple

kb = int(2**10)
MAX_BOX_SIZE = 16 * kb
BOX_MBR = 2500
BOX_BYTES = 400


PageIndicies = abi.StaticArray[abi.Uint8, Literal[32]]


class SparseArray:
    def __init__(self, key: str, t: NamedTuple, size: int):
        self.key = key
        self.t = t
        self.element_size = abi.sizeof(t.get_type())
        self.pages = abi.make(abi.DynamicArray[PageIndicies])

    def initialize(self) -> Expr:
        """initialize creates the box to hold pages of array elements"""
        return BoxCreate(Bytes(f"{self.key}-pages"), Int(MAX_BOX_SIZE))

    def alloc(self) -> Expr:
        """Create a new Box to use for storage"""
        return Seq(
            self.pages.decode(self.get_page_indicies()),
            (page_name := ScratchVar()).store(
                self.page_name(Suffix(Itob(self.pages.length()), Int(7))),
            ),
            BoxCreate(
                page_name.load(),
                Int(MAX_BOX_SIZE),
            ),
            page_name.load(),
        )

    def dealloc(self, page: Expr) -> Expr:
        """Deletes Box from storage, used when we dont need it anymore"""
        return BoxDelete(self.page_name(page))

    def get_page_indicies(self) -> Expr:
        """Read in all the page indicies"""
        return BoxExtract(
            Bytes(f"{self.key}-pages"),
            Int(0),
            Int(int(MAX_BOX_SIZE / 4)),
        )

    def write_page_indicies(self, page: Expr) -> Expr:
        """Write out page indicies"""
        return BoxReplace(Bytes(f"{self.key}-pages"), Int(0), page)

    def page_name(self, page: Expr) -> Expr:
        """Page name is key + page"""
        return Concat(Bytes(self.key), page)

    def reserve_slot(self) -> Expr:
        """Find first open slot"""
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
                ),
            ),
            # Return slot = [page, index]
            Concat(
                Suffix(Itob(page.load()), Int(7)), Suffix(Itob(index.load()), Int(7))
            ),
        )

    def put(self, slot: abi.Uint16, t: "NamedTuple") -> Expr:
        """Write T into slot"""
        return Seq(
            (page := abi.Uint8()).decode(Extract(slot.encode(), Int(0), Int(1))),
            (idx := abi.Uint8()).decode(Extract(slot.encode(), Int(1), Int(1))),
            BoxReplace(
                self.page_name(page.encode()),
                Int(self.element_size) * idx.get(),
                t.encode(),
            ),
        )

    def get(self, slot: abi.Uint16) -> Expr:
        """Get T from slot"""
        return Seq(
            (page := abi.Uint8()).decode(Extract(slot.encode(), Int(0), Int(1))),
            (idx := abi.Uint8()).decode(Extract(slot.encode(), Int(1), Int(1))),
            BoxExtract(
                self.page_name(page.encode()),
                Int(self.element_size) * idx.get(),
                Int(self.element_size) * (idx.get() + Int(1)),
            ),
        )

    def delete(self, slot: abi.Uint16) -> Expr:
        pass
