from typing import List
from pyteal import *
from application import *
from models import *
from priority_queue import PriorityQueue

kb = 2 ** 10
box_size = Int(32 * kb)


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
        # Used by pq
        GlobalStorageValue("resting_orders", TealType.uint64),
        # GlobalStorageValue("resting_asks", TealType.uint64),
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


vex = Vex(router)

ask_pq = PriorityQueue(Bytes("ask_book"), box_size, Int(1), RestingOrderType)
bid_pq = PriorityQueue(Bytes("bid_book"), box_size, Int(0), RestingOrderType)


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


router.add_method_handler(bootstrap)
router.add_method_handler(new_order)
router.add_method_handler(peek_root)
router.add_method_handler(fill_root)
router.add_method_handler(read_order)
router.add_method_handler(cancel_order)

if __name__ == "__main__":
    import os
    import json

    approval, clear, spec = router.compile_program(
        version=7,
        assembleConstants=True,
        optimize=OptimizeOptions(scratch_slots=True),
    )

    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, "abi.json"), "w") as f:
        f.write(json.dumps(spec.dictify(), indent=2))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(approval)

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(clear)
