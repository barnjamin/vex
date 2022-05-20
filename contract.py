from pyteal import *
from models import *


router = Router()
router.add_bare_call(Approve(), OnComplete.NoOp, creation=True)
router.add_bare_call(
    Return(Txn.sender() == Global.creator_address()),
    [OnComplete.UpdateApplication, OnComplete.DeleteApplication],
)
router.add_bare_call(
    Reject(), [OnComplete.OptIn, OnComplete.ClearState, OnComplete.CloseOut]
)


@router.add_method_handler
@ABIReturnSubroutine
def boostrap():
    return Seq(init_orderbook())

OrderBookType = OrderBook().get_type()

@router.add_method_handler
@ABIReturnSubroutine
def get_orderbook(*, output: OrderBookType):
    return Seq(
        output.decode(read_orderbook())
    )


# @router.add_method_handler
# @ABIReturnSubroutine
# def new_order(order: IncomingOrder, *, output: abi.String):
#    return Seq(
#        (ob := OrderBook()).decode(get_orderbook()),
#        BoxCreate(get_price_queue_key(order.Price), Int(1024)),
#        BoxReplace(key.get(), Int(0), Bytes("abc123")),
#        output.set(BoxExtract(key.get(), Int(0), Int(3))),
#        BoxDelete(key.get()),
#    )

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
