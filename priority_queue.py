from pyteal import *

resting_orders_key = Bytes("resting_orders")


class PriorityQueue:
    def __init__(self, box_name: Bytes, box_size: Int, type_spec: abi.TypeSpec):
        self.box_name = box_name
        self.box_size = box_size
        self.type_spec = type_spec
        self.type_size = Int(abi.size_of(self.type_spec))

    def count(self) -> Expr:
        """count returns the number of elements in the priority queue"""
        return pq_count()

    def insert(self, thing: abi.BaseType) -> Expr:
        """insert adds a new element in sorted order"""
        return pq_insert(self.box_name, thing.encode())

    def delete(self, thing: abi.BaseType) -> Expr:
        """delete removes a given element by finding it in the pq then removing it by index"""
        return Seq((idx := abi.Uint64()).set(self.search(thing)), self.remove(idx))

    def peek(self) -> Expr:
        """peak reads the root element but doesn't modify the pq"""
        return pq_read(self.box_name, Int(0), self.type_size)

    def pop(self) -> Expr:
        """pop removes the first element from the pq and returns it after resorting the pq"""
        return pq_pop(self.box_name, self.type_size)

    def remove(self, idx: abi.Uint64) -> Expr:
        """remove removes an element by its index"""
        return pq_remove(self.box_name, idx.get(), self.type_size)

    def get(self, idx: abi.Uint64) -> Expr:
        """get returns an element at a given index"""
        return pq_read(self.box_name, idx.get(), self.type_size)

    def search(self, thing: abi.BaseType) -> Expr:
        """search tries to find the element in the pq"""
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
def pq_insert(key, val):
    return Seq(
        # Write the first element in the last spot
        pq_write(key, pq_count(), val),
        # Restore heap invariant starting with the last element
        pq_upheap(key, pq_count(), Len(val)),
        # Increment the counter
        pq_count_incr(),
    )


@Subroutine(TealType.none)
def pq_swap(key, aidx, bidx, len):
    return Seq(
        # Store a and b in scratch
        (a := ScratchVar()).store(pq_read(key, aidx, len)),
        (b := ScratchVar()).store(pq_read(key, bidx, len)),
        # Write b to a index
        pq_write(key, bidx, a.load()),
        # Write a to b index
        pq_write(key, aidx, b.load()),
    )


@Subroutine(TealType.bytes)
def pq_pop(key, len):
    return Seq(
        # Read the top element
        (top := ScratchVar()).store(BoxExtract(key, Int(0), len)),
        # Decrement the counter so we have the right last element
        pq_count_decr(),
        # Swap last for first
        pq_swap(key, Int(0), pq_count(), len),
        # Restore heap property
        pq_downheap(key, Int(0), len),
        # Zero out bytes for the last one
        pq_zero(key, pq_count(), len),
        # Return the top element
        top.load(),
    )


@Subroutine(TealType.none)
def pq_remove(key, idx, len):
    return Seq(
        # Decrement the counter
        pq_count_decr(),
        # Swap the index to remove for last
        pq_swap(key, idx, pq_count(), len),
        # Restore heap invariant
        pq_downheap(key, idx, len),
        # Zero out bytes for the last one (the one we're removing)
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
    """pq_upheap restores the heap invariant property starting from a given index up the heap
    by comparing the child with its parent, if needed, we swap the items and check again
    """
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
    """pq_downheap restores the heap invariant property starting from a given index down the heap
    by comparing a parent with its children, if one or the other is larger we swap the items and check again
    we preferr to swap the right element if both are larger
    """
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
