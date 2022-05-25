from typing import Type
from pyteal import *


resting_orders_key = Bytes("resting_orders")

##### pq counter stored in global state
@Subroutine(TealType.uint64)
def pq_count():
    return App.globalGet(resting_orders_key)


@Subroutine(TealType.none)
def pq_count_incr():
    return App.globalPut(resting_orders_key, pq_count() + Int(1))


@Subroutine(TealType.none)
def pq_count_decr():
    return App.globalPut(resting_orders_key, pq_count() - Int(1))


#### pq read/writes
@Subroutine(TealType.none)
def pq_insert(key, pos, val):
    return Seq(
        BoxReplace(key, pos, val), 
        pq_upheap(key, pos, Len(val)), 
        pq_count_incr()
    )


@Subroutine(TealType.none)
def pq_swap(key, apos, bpos, len):
    return Seq(
        (a := ScratchVar()).store(BoxExtract(key, apos, len)),
        (b := ScratchVar()).store(BoxExtract(key, bpos, len)),
        BoxReplace(key, bpos, a.load()),
        BoxReplace(key, apos, b.load()),
    )


@Subroutine(TealType.bytes)
def pq_pop(key, len):
    return Seq(
        (top := ScratchVar()).store(BoxExtract(key, Int(0), len)),
        pq_swap(key, Int(0), pq_count(), len),
        pq_downheap(key, Int(0), len),
        pq_count_decr(),
        top.load(),
    )


@Subroutine(TealType.bytes)
def pq_read(key, pos, len):
    return BoxExtract(key, pos, len)

def child_pos_left(pos)->Expr:
    return pos * Int(2)

def child_pos_right(pos)->Expr:
    return (pos * Int(2)) + Int(1)

def parent_pos(pos)->Expr:
    return If(pos % Int(2) == Int(0), (pos - Int(1)), pos) / Int(2)


@Subroutine(TealType.uint64)
def sort_key(v)->Expr:
    return Int(0)

@Subroutine(TealType.none)
def pq_upheap(key, pos, len):
    return If(pos != Int(0), Seq(
        (smallest := ScratchVar()).store(pos),
        While(smallest.load()>Int(0)).Do(
            Seq(
                (curr_val := ScratchVar()).store(pq_read(key, pos, len)),
                (p_pos := ScratchVar()).store(parent_pos(smallest.load())),
                (p_val := ScratchVar()).store(pq_read(key, p_pos.load(), len)),
                If(sort_key(curr_val.load()) < sort_key(p_val.load()), Seq(
                    pq_swap(key, smallest.load(), p_pos.load(), len),
                    smallest.store(p_pos.load())
                ), smallest.store(Int(0)))
            )
        )
    ))


@Subroutine(TealType.none)
def pq_downheap(key, pos, len):
    return Seq(
        (largest := ScratchVar()).store(pos),
        While(largest.load() > Int(0)).Do(
            Seq(
                (curr_pos := ScratchVar()).store(largest.load()),
                (curr_val := ScratchVar()).store(pq_read(key, largest.load(), len)),
                (left_pos := ScratchVar()).store(child_pos_left(largest.load())),
                (left_val := ScratchVar()).store(
                    If(
                        left_pos.load() < pq_count(),
                        pq_read(key, left_pos.load(), len),
                        Bytes(""),
                    )
                ),
                (right_pos := ScratchVar()).store(child_pos_right(largest.load())),
                (right_val := ScratchVar()).store(
                    If(
                        right_pos.load() < pq_count(),
                        pq_read(key, right_pos.load(), len),
                        Bytes(""),
                    )
                ),
                If(
                    sort_key(curr_val.load()) > sort_key(left_val.load()),
                    largest.store(left_pos.load()),
                ),
                If(
                    sort_key(curr_val.load()) > sort_key(right_val.load()),
                    largest.store(right_pos.load()),
                ),
                If(
                    largest.load() != curr_pos.load(),
                    Seq(
                        pq_swap(key, curr_pos.load(), largest.load(), len),
                    ),
                    largest.store(Int(0)),
                ),
            )
        ),
    )


class PriorityQueue:
    def __init__(self, box_name: Bytes, box_size: Int, type_spec: abi.TypeSpec):
        self.box_name = box_name
        self.box_size = box_size
        self.type_spec = type_spec 
        self.type_size = Int(abi.size_of(self.type_spec))

    def count(self) -> Expr:
        return pq_count()

    def insert(self, thing: abi.BaseType) -> Expr:
        return pq_insert(self.box_name, pq_count() * self.type_size, thing.encode())

    def peek(self):
        return pq_read(self.box_name, Int(0), self.type_size)

    def pop(self):
        return pq_pop(self.box_name, self.type_size)

    def remove(self, thing: abi.BaseType) -> Expr:
        pass
        # return pq_delete(self.box_name, )

    def search(self):
        pass
