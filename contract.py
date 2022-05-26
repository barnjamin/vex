from pyteal import *

from models import *
from priority_queue import PriorityQueue


kb = 2 ** 10
box_size = Int(32 * kb)

seq_key = Bytes("sequence")
ask_book_key = Bytes("ask_book")
bid_book_key = Bytes("bid_book")

ASK_SORT = Int(1)
BID_SORT = Int(0)

ask_pq = PriorityQueue(ask_book_key, box_size, ASK_SORT, RestingOrderType)
bid_pq = PriorityQueue(bid_book_key, box_size, ASK_SORT, RestingOrderType)

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


@ABIReturnSubroutine
def bootstrap():
    return Seq(
        BoxCreate(ask_book_key, box_size),
        BoxCreate(bid_book_key, box_size),
        App.globalPut(seq_key, Int(0)),
    )


router.add_method_handler(bootstrap)


@Subroutine(TealType.uint64)
def assign_sequence():
    return Seq(
        (sv := ScratchVar()).store(App.globalGet(seq_key)),
        App.globalPut(seq_key, sv.load() + Int(1)),
        sv.load(),
    )


@ABIReturnSubroutine
def new_order(order: IncomingOrderType):
    return Seq(
        (io := IncomingOrder()).decode(order.encode()),
        (p := abi.Uint64()).set(io.price()),
        (s := abi.Uint64()).set(io.size()),
        (seq := abi.Uint64()).set(assign_sequence()),
        (resting_order := abi.make(RestingOrderType)).set(p, seq, s),
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
