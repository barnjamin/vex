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


@ABIReturnSubroutine
def bootstrap():
    return Seq(vex.initialize_globals(), ask_pq.initialize(), bid_pq.initialize())


@ABIReturnSubroutine
def new_order(order: IncomingOrderType):
    return Seq(
        (io := IncomingOrder()).decode(order.encode()),
        (p := abi.Uint64()).set(io.price()),
        (s := abi.Uint64()).set(io.size()),
        (seq := abi.Uint64()).set(assign_sequence()),
        (resting_order := abi.make(RestingOrderType)).set(p, seq, s),
        # while incoming order is unfilled,
        #   peek next order and pop if match
        bid_pq.insert(resting_order),
    )


@ABIReturnSubroutine
def peek_root(*, output: RestingOrderType):
    return output.decode(bid_pq.peek())


@ABIReturnSubroutine
def fill_root(*, output: RestingOrderType):
    return output.decode(bid_pq.pop())


@ABIReturnSubroutine
def read_order(idx: abi.Uint64, *, output: RestingOrderType):
    return output.decode(bid_pq.get(idx))


@ABIReturnSubroutine
def cancel_order(ro: RestingOrderType):
    return bid_pq.delete(ro)


vex.router.add_method_handler(bootstrap)
vex.router.add_method_handler(new_order)
vex.router.add_method_handler(peek_root)
vex.router.add_method_handler(fill_root)
vex.router.add_method_handler(read_order)
vex.router.add_method_handler(cancel_order)