from pyteal import *

from models import NamedTuple
from priority_queue import PriorityQueue


kb = 2 ** 10
box_size = Int(16 * kb)

seq_key = Bytes("sequence")
book_key = Bytes("book")


router = Router(
    "vex",
    OnCompleteActions(
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
    return Seq(BoxCreate(book_key, box_size), App.globalPut(seq_key, Int(0)))


router.add_method_handler(bootstrap)


class IncomingOrder(NamedTuple):
    price: abi.Uint64
    size: abi.Uint64


IncomingOrderType = IncomingOrder().get_type()


class RestingOrder(NamedTuple):
    price: abi.Uint64
    sequence: abi.Uint64
    size: abi.Uint64


RestingOrderType = RestingOrder().get_type()

pq = PriorityQueue(book_key, box_size, RestingOrderType)


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
        pq.insert(resting_order),
    )


router.add_method_handler(new_order)


@ABIReturnSubroutine
def peek_root(*, output: RestingOrderType):
    return output.decode(pq.peek())


router.add_method_handler(peek_root)


@ABIReturnSubroutine
def fill_root(*, output: RestingOrderType):
    return output.decode(pq.pop())


router.add_method_handler(fill_root)


@ABIReturnSubroutine
def read_order(idx: abi.Uint64, *, output: RestingOrderType):
    return output.decode(pq.get(idx))


router.add_method_handler(read_order)


@ABIReturnSubroutine
def cancel_order(ro: RestingOrderType):
    return pq.delete(ro)


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
