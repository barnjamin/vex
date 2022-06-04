from pyteal import *
from priority_queue import PriorityQueue
from models import *

kb = 2 ** 10
box_size = Int(32 * kb)

ask_pq = PriorityQueue("ask_book", box_size, Int(1), RestingOrderType)
bid_pq = PriorityQueue("bid_book", box_size, Int(0), RestingOrderType)


@Subroutine(TealType.none)
def add_bid(price: abi.Uint64, size: abi.Uint64, seq: Expr):
    return Seq(
        (s := abi.Uint64()).set(seq),
        (resting_order := RestingOrder()).set(price, s, size),
        bid_pq.insert(resting_order),
    )


@Subroutine(TealType.none)
def add_ask(price: abi.Uint64, size: abi.Uint64, seq: Expr):
    return Seq(
        (s := abi.Uint64()).set(seq),
        (resting_order := RestingOrder()).set(price, s, size),
        ask_pq.insert(resting_order),
    )


@Subroutine(TealType.uint64)
def try_fill_bids(price: Expr, size: Expr):
    return Seq(
        # If theres nothing in the book or empty size, dip
        If(Or(bid_pq.count() == Int(0), size == Int(0)), Return(size)),
        # Peek the book and try to fill
        (ro := RestingOrder()).decode(bid_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        # Next order not fillable
        If(resting_price.get() < price, Return(size)),
        If(
            # Is it a full or partial of resting
            resting_size.get() <= size,
            Seq(
                # Full fill of resting
                bid_pq.remove(Int(0)),
                try_fill_bids(price, size - resting_size.get()),
            ),
            Seq(
                # Partial fill of resting
                (seq := abi.Uint64()).set(ro.sequence()),
                (new_size := abi.Uint64()).set(resting_size.get() - size),
                ro.set(resting_price, seq, new_size),
                # Update resting with new size
                bid_pq.update(Int(0), ro),
                # Return 0 for size left fo fill
                Int(0),
            ),
        ),
    )


@Subroutine(TealType.uint64)
def try_fill_asks(price: Expr, size: Expr):
    return Seq(
        # If theres nothing in the book or empty size, dip
        If(Or(ask_pq.count() == Int(0), size == Int(0)), Return(size)),
        # Peek the book and try to fill
        (ro := RestingOrder()).decode(ask_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        # Next order not fillable
        If(resting_price.get() > price, Return(size)),
        If(
            # Is it a full or partial of resting
            resting_size.get() <= size,
            Seq(
                # Full fill of resting
                ask_pq.remove(Int(0)),
                try_fill_asks(price, size - resting_size.get()),
            ),
            Seq(
                # Partial fill of resting
                (seq := abi.Uint64()).set(ro.sequence()),
                (new_size := abi.Uint64()).set(resting_size.get() - size),
                ro.set(resting_price, seq, new_size),
                # Update resting with new size
                ask_pq.update(Int(0), ro),
                # Return 0 for size left fo fill
                Int(0),
            ),
        ),
    )
