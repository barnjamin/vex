from pyteal import *

from models import NamedTuple
from priority_queue import PriorityQueue


kb = 2 ** 10
box_size = Int(16 * kb)

seq_key = Bytes("sequence")
book_key = Bytes("book")


router = Router(
    "vex",
    OCActions(
        no_op=OCAction.create_only(Approve()),
        update_application=OCAction.always(
            Return(Txn.sender() == Global.creator_address())
        ),
        delete_application=OCAction.always(
            Return(Txn.sender() == Global.creator_address())
        ),
        opt_in=OCAction.always(Reject()),
        clear_state=OCAction.always(Reject()),
        close_out=OCAction.always(Reject()),
    ),
)


@ABIReturnSubroutine
def bootstrap():
    return Seq(BoxCreate(book_key, box_size), App.globalPut(seq_key, Int(0)))


router.add_method_handler(bootstrap)

class Order(NamedTuple):
    price: abi.Uint64
    size: abi.Uint64


OrderType = Order().get_type()

pq = PriorityQueue(book_key, box_size, OrderType)

@ABIReturnSubroutine
def new_order(order: OrderType, *, output: OrderType):
    return Seq(
        pq.insert(order),

        # Works
        #(sv := ScratchVar()).store(BoxExtract(Bytes("book"), Int(0), Int(16))),
        # Also works
        #(sv := ScratchVar()).store(get_first()),

        # Doesn't work? logic eval error: stack finished with bytes not int. Details: pc=448, opcodes=
        (sv := ScratchVar()).store(read_first()),

        output.decode(sv.load())
    )

def read_first():
    return BoxExtract(Bytes("book"), Int(0), Int(16))

@Subroutine(TealType.bytes)
def get_first():
    return Seq(
        (p := abi.Uint64()).set(100),
        (s := abi.Uint64()).set(1),
        (o := Order()).set(p, s),
        o.encode()
    )

router.add_method_handler(new_order)

#@ABIReturnSubroutine
#def read_root():
#    return Seq(
#        Log(Itob(pq.peek()))
#    )
#router.add_method_handler(read_root)

if __name__ == "__main__":
    import os
    import json

    path = os.path.dirname(os.path.abspath(__file__))

    approval, clear, spec = router.build_program()

    with open(os.path.join(path, "abi.json"), "w") as f:
        f.write(json.dumps(spec))

    with open(os.path.join(path, "approval.teal"), "w") as f:
        f.write(
            compileTeal(
                approval,
                mode=Mode.Application,
                version=7,
                assembleConstants=True,
                optimize=OptimizeOptions(scratch_slots=True),
            )
        )

    with open(os.path.join(path, "clear.teal"), "w") as f:
        f.write(
            compileTeal(
                clear,
                mode=Mode.Application,
                version=7,
                assembleConstants=True,
                optimize=OptimizeOptions(scratch_slots=True),
            )
        )
