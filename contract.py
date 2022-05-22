from pyteal import *
from models import *
from operations import *
from persistent_sparse_array import *
from vex import *



oc = OnCompleteActions().set_action(
    Approve(), OnComplete.NoOp, create=True
).set_action(
    Return(Txn.sender() == Global.creator_address()),
    OnComplete.UpdateApplication
).set_action(
   Return(Txn.sender() == Global.creator_address()),
   OnComplete.DeleteApplication,
).set_action(
    Reject(), OnComplete.OptIn
).set_action(
    Reject(), OnComplete.ClearState
).set_action(
    Reject(), OnComplete.CloseOut
)

order_doofus = Doofus("orders", RestingOrder())

router = Router("vex", oc)

vex = Vex()

@router.abi_method()
def boostrap():
    return Seq(
        # 
        order_doofus.initialize(),
        # Init global vars
        vex.init_globals(),
    )

IncomingOrderType = IncomingOrder().get_type()


@router.abi_method()
def new_order(order: IncomingOrderType, *, output: abi.Uint16):
    return Seq(
        (io := IncomingOrder()).decode(order.encode()),
        (last_slot := abi.Uint16()).decode(vex.Global[BOTTOM_BID_PTR].get()),
        (addr := abi.Address()).set(Txn.accounts[0]),
        (size := abi.Uint64()).set(io.size()),
        (lower := abi.Uint16()).set(0),
        (sequence := abi.Uint64()).set(0),
        (ro := RestingOrder()).set(
            addr,
            size,
            sequence,
            last_slot,
            lower,
        ),
        (new_slot := abi.Uint16()).decode(order_doofus.reserve_slot()),
        order_doofus.write(new_slot, ro),
        output.set(new_slot),
    )

@router.abi_method()
def read_order(slot: abi.Uint16, *, output: RestingOrderType):
    return output.decode(order_doofus.read(slot))


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
