from pyteal import *

resting_orders_key = Bytes("resting_orders")


class PriorityQueue:
    def __init__(self, box_name: Bytes, box_size: Int, type_spec: abi.TypeSpec):
        self.box_name = box_name
        self.box_size = box_size
        self.type_spec = type_spec
        self.type_size = Int(abi.size_of(self.type_spec))

    def count(self) -> Expr:
        return pq_count()

    def insert(self, thing: abi.BaseType) -> Expr:
        return pq_insert(self.box_name, pq_count(), thing.encode())

    def delete(self, thing: abi.BaseType) -> Expr:
        return Seq((idx := abi.Uint64()).set(self.search(thing)), self.remove(idx))

    def peek(self) -> Expr:
        return pq_read(self.box_name, Int(0), self.type_size)

    def pop(self) -> Expr:
        return pq_pop(self.box_name, self.type_size)

    def remove(self, idx: abi.Uint64) -> Expr:
        return pq_remove(self.box_name, idx.get(), self.type_size)

    def get(self, idx: abi.Uint64) -> Expr:
        return pq_read(self.box_name, idx.get(), self.type_size)

    def search(self, thing: abi.BaseType) -> Expr:
        return pq_search(self.box_name, thing.encode())


##### pq counter stored in global state
def pq_count():
    return App.globalGet(resting_orders_key)


def pq_count_incr():
    return App.globalPut(resting_orders_key, pq_count() + Int(1))


def pq_count_decr():
    return App.globalPut(resting_orders_key, pq_count() - Int(1))


# pq idx helpers
def child_idx_left(pos) -> Expr:
    return pos * Int(2)


def child_idx_right(pos) -> Expr:
    return (pos * Int(2)) + Int(1)


def parent_idx(pos) -> Expr:
    return If(pos % Int(2) == Int(0), (pos - Int(1)), pos) / Int(2)


#### pq read/writes
def pq_write(key, idx, val):
    return BoxReplace(key, idx * Len(val), val)


def pq_read(key, idx, len):
    return BoxExtract(key, idx * len, len)


def pq_zero(key, idx, len):
    return pq_write(key, idx, BytesZero(len))


## pq operations
@Subroutine(TealType.none)
def pq_insert(key, idx, val):
    return Seq(pq_write(key, idx, val), pq_upheap(key, idx, Len(val)), pq_count_incr())


@Subroutine(TealType.none)
def pq_swap(key, aidx, bidx, len):
    return Seq(
        (a := ScratchVar()).store(pq_read(key, aidx, len)),
        (b := ScratchVar()).store(pq_read(key, bidx, len)),
        pq_write(key, bidx, a.load()),
        pq_write(key, aidx, b.load()),
    )


@Subroutine(TealType.bytes)
def pq_pop(key, len):
    return Seq(
        (top := ScratchVar()).store(BoxExtract(key, Int(0), len)),
        pq_count_decr(),
        pq_swap(key, Int(0), pq_count(), len),
        pq_downheap(key, Int(0), len),
        pq_zero(key, pq_count(), len),
        top.load(),
    )


@Subroutine(TealType.none)
def pq_remove(key, idx, len):
    return Seq(
        pq_count_decr(),
        pq_swap(key, idx, pq_count(), len),
        pq_downheap(key, idx, len),
        pq_zero(key, pq_count(), len),
    )


@Subroutine(TealType.uint64)
def pq_search(key, val):
    i = ScratchVar()
    init = i.store(Int(0))
    cond = i.load() < pq_count()
    iter = i.store(i.load() + Int(1))
    return Seq(
        For(init, cond, iter).Do(
            If(val == pq_read(key, i.load(), Len(val)), Return(i.load()))
        ),
        i.load(),
    )


# pq Heap invariant restoring
@Subroutine(TealType.uint64)
def sorted_lt(a, b) -> Expr:
    """sorted_lt checks to see if a is less than b by comparing the price|sequence both uint64"""
    return BytesLt(Extract(a, Int(0), Int(2 * 8)), Extract(b, Int(0), Int(2 * 8)))


@Subroutine(TealType.none)
def pq_upheap(key, idx, len):
    return If(
        idx != Int(0),
        Seq(
            (smallest := ScratchVar()).store(idx),
            While(smallest.load() > Int(0)).Do(
                Seq(
                    (curr_val := ScratchVar()).store(
                        pq_read(key, smallest.load(), len)
                    ),
                    (p_pos := ScratchVar()).store(parent_idx(smallest.load())),
                    (p_val := ScratchVar()).store(pq_read(key, p_pos.load(), len)),
                    If(
                        sorted_lt(curr_val.load(), p_val.load()),
                        Seq(
                            pq_swap(key, smallest.load(), p_pos.load(), len),
                            smallest.store(p_pos.load()),
                        ),
                        smallest.store(Int(0)),
                    ),
                )
            ),
        ),
    )


@Subroutine(TealType.none)
def pq_downheap(key, idx, len):
    return Seq(
        (largest := ScratchVar()).store(idx),
        (sorted := ScratchVar()).store(Int(1)),
        While(sorted.load()).Do(
            Seq(
                (curr_idx := ScratchVar()).store(largest.load()),
                (curr_val := ScratchVar()).store(pq_read(key, curr_idx.load(), len)),
                # Check the left side first
                (left_idx := ScratchVar()).store(child_idx_left(curr_idx.load())),
                (left_val := ScratchVar()).store(
                    If(
                        left_idx.load() < pq_count(),
                        pq_read(key, left_idx.load(), len),
                        BytesNot(BytesZero(len)),
                    )
                ),
                If(
                    Not(sorted_lt(curr_val.load(), left_val.load())),
                    largest.store(left_idx.load()),
                ),
                # Check the right side second
                (right_idx := ScratchVar()).store(child_idx_right(curr_idx.load())),
                (right_val := ScratchVar()).store(
                    If(
                        right_idx.load() < pq_count(),
                        pq_read(key, right_idx.load(), len),
                        BytesNot(BytesZero(len)),
                    )
                ),
                If(
                    Not(sorted_lt(curr_val.load(), right_val.load())),
                    largest.store(right_idx.load()),
                ),
                # If largest is now different than current swap them and start over
                If(
                    largest.load() != curr_idx.load(),
                    pq_swap(key, curr_idx.load(), largest.load(), len),
                    sorted.store(Int(0)),
                ),
            )
        ),
    )
