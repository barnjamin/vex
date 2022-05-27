from re import I
from typing import List
from pyteal import *
from application import *
from models import *
from priority_queue import PriorityQueue

kb = 2 ** 10
box_size = Int(32 * kb)

ask_pq = PriorityQueue("ask_book", box_size, Int(1), RestingOrderType)
bid_pq = PriorityQueue("bid_book", box_size, Int(0), RestingOrderType)


class Vex(Application):
    globals: List[GlobalStorageValue] = [
        # Static Config
        GlobalStorageValue("asset_a", TealType.uint64, immutable=True),
        GlobalStorageValue("asset_b", TealType.uint64, immutable=True),
        GlobalStorageValue("lot_a", TealType.uint64, immutable=True),
        GlobalStorageValue("lot_b", TealType.uint64, immutable=True),
        GlobalStorageValue("decimals", TealType.uint64, immutable=True),
        # Updated as needed
        GlobalStorageValue("seq", TealType.uint64),
        GlobalStorageValue("bid", TealType.uint64),
        GlobalStorageValue("ask", TealType.uint64),
        GlobalStorageValue("mid", TealType.uint64),
    ]

    locals: List[LocalStorageValue] = [
        LocalStorageValue("bal_a", TealType.uint64),
        LocalStorageValue("bal_b", TealType.uint64),
        LocalStorageValue("orders", TealType.bytes),
    ]

    router = Router(
        "vex",
        BareCallActions(
            no_op=OnCompleteAction.create_only(Approve()),
            update_application=OnCompleteAction.always(
                Return(Txn.sender() == Global.creator_address())
            ),
            delete_application=OnCompleteAction.always(
                Return(Txn.sender() == Global.creator_address())
            ),
            opt_in=OnCompleteAction.always(Reject()),
            clear_state=OnCompleteAction.always(Reject()),
            close_out=OnCompleteAction.always(Reject()),
        ),
    )


vex = Vex()

# Appending to globals array _after_ init means they're not set as attributes
vex.globals.append(GlobalStorageValue(ask_pq.box_name_str, TealType.uint64))
vex.globals.append(GlobalStorageValue(bid_pq.box_name_str, TealType.uint64))


@Subroutine(TealType.uint64)
def assign_sequence():
    return Seq(
        (sv := ScratchVar()).store(vex.seq),
        vex.seq(sv.load() + Int(1)),
        sv.load(),
    )


@Subroutine(TealType.uint64)
def try_fill_bids(price: Expr, size: Expr):
    return Seq(
        # If theres nothing in the book, dip
        If(bid_pq.count() == Int(0), Return(size)),
        # Setup stuff for looping
        (unfilled := ScratchVar()).store(size),
        (ro := RestingOrder()).decode(bid_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        While(
            And(
                bid_pq.count() > Int(0),
                unfilled.load() > Int(0),
                resting_price.get() >= price,
            )
        ).Do(
            Seq(
                (seq := abi.Uint64()).set(ro.sequence()),
                resting_price.set(ro.price()),
                resting_size.set(ro.size()),
                If(
                    resting_size.get() > unfilled.load(),
                    Seq(
                        # Partial fill
                        (new_size := abi.Uint64()).set(
                            resting_size.get() - unfilled.load()
                        ),
                        ro.set(resting_price, new_size, seq),
                        bid_pq.update(Int(0), ro),
                        unfilled.store(Int(0)),
                    ),
                    Seq(
                        # Full fill
                        bid_pq.remove(Int(0)),
                        unfilled.store(unfilled.load() - resting_size.get()),
                        ro.decode(bid_pq.peek()),
                    ),
                ),
            )
        ),
        unfilled.load(),
    )


@Subroutine(TealType.uint64)
def try_fill_asks(price: Expr, size: Expr):
    return Seq(
        # If theres nothing in the book, dip
        If(ask_pq.count() == Int(0), Return(size)),
        # Setup stuff for looping
        (unfilled := ScratchVar()).store(size),
        (ro := RestingOrder()).decode(ask_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        While(
            And(
                ask_pq.count() > Int(0),
                unfilled.load() > Int(0),
                resting_price.get() <= price,
            )
        ).Do(
            Seq(
                (seq := abi.Uint64()).set(ro.sequence()),
                resting_price.set(ro.price()),
                resting_size.set(ro.size()),
                If(
                    resting_size.get() > unfilled.load(),
                    Seq(
                        # Partial fill of resting
                        (new_size := abi.Uint64()).set(
                            resting_size.get() - unfilled.load()
                        ),
                        ro.set(resting_price, new_size, seq),
                        ask_pq.update(Int(0), ro),
                        unfilled.store(Int(0)),
                    ),
                    Seq(
                        # Full fill of resting
                        ask_pq.remove(Int(0)),
                        unfilled.store(unfilled.load() - resting_size.get()),
                        ro.decode(ask_pq.peek()),
                    ),
                ),
            )
        ),
        unfilled.load(),
    )


@vex.router.method
def bootstrap():
    return Seq(vex.initialize_globals(), ask_pq.initialize(), bid_pq.initialize())


@vex.router.method
def new_order(order: IncomingOrderType, *, output: abi.Uint64):
    return Seq(
        (io := IncomingOrder()).decode(order.encode()),
        (bid_side := abi.Bool()).set(io.bid_side()),
        (price := abi.Uint64()).set(io.price()),
        (size := abi.Uint64()).set(io.size()),
        (remaining_size := abi.Uint64()).set(io.size()),
        If(
            bid_side.get(),
            Seq(
                remaining_size.set(try_fill_bids(price.get(), size.get())),
                If(
                    remaining_size.get() > Int(0),
                    Seq(
                        (seq := abi.Uint64()).set(assign_sequence()),
                        (resting_order := RestingOrder()).set(
                            price, seq, remaining_size
                        ),
                        bid_pq.insert(resting_order),
                    ),
                ),
            ),
            Seq(
                remaining_size.set(try_fill_asks(price.get(), size.get())),
                If(
                    remaining_size.get() > Int(0),
                    Seq(
                        (seq := abi.Uint64()).set(assign_sequence()),
                        (resting_order := RestingOrder()).set(
                            price, seq, remaining_size
                        ),
                        ask_pq.insert(resting_order),
                    ),
                ),
            ),
        ),
        output.set(size.get() - remaining_size.get()),
    )
