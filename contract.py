from pyteal import *
from models import *
from operations import *
from application import *
from persistent_sparse_array import *

ASSET_A = "asset_a"
ASSET_B = "asset_b"
MX_PG_PRICE = "mx_pg_price"
P_DECIMALS = "p_decimals"
MX_WDTH_MKT = "mx_wdth_mkt"
MN_SZ = "mn_sz"
BID = "bid"
ASK = "ask"
MID = "mid"
TOP_BID_PTR = "top_bid_ptr"
BOTTOM_BID_PTR = "bottom_bid_ptr"
TOP_ASK_PTR = "top_ask_ptr"
BOTTOM_ASK_PTR = "bottom_ask_ptr"
SEQUENCE = "sequence"

BALANCE_A = "balance_a"
BALANCE_B = "balance_b"
ORDERS = "orders"


class Vex(AppState):
    Global: Dict[str, GlobalStorageValue] = {
        # Static Settings
        ASSET_A: GlobalStorageValue(ASSET_A, abi.Uint64(), immutable=True),
        ASSET_B: GlobalStorageValue(ASSET_B, abi.Uint64(), immutable=True),
        MX_PG_PRICE: GlobalStorageValue(MX_PG_PRICE, abi.Uint8()),
        P_DECIMALS: GlobalStorageValue(P_DECIMALS, abi.Uint8()),
        MX_WDTH_MKT: GlobalStorageValue(MX_WDTH_MKT, abi.Uint32()),
        MN_SZ: GlobalStorageValue(MN_SZ, abi.Uint64()),
        BID: GlobalStorageValue(BID, abi.Uint64()),
        ASK: GlobalStorageValue(ASK, abi.Uint64()),
        MID: GlobalStorageValue(MID, abi.Uint64()),
        TOP_BID_PTR: GlobalStorageValue(TOP_BID_PTR, abi.Uint64()),
        BOTTOM_BID_PTR: GlobalStorageValue(BOTTOM_BID_PTR, abi.Uint64()),
        TOP_ASK_PTR: GlobalStorageValue(TOP_ASK_PTR, abi.Uint64()),
        BOTTOM_ASK_PTR: GlobalStorageValue(BOTTOM_ASK_PTR, abi.Uint64()),
        SEQUENCE: GlobalStorageValue(SEQUENCE, abi.Uint64())
    }

    Local: Dict[str, LocalStorageValue] = {
        BALANCE_A: LocalStorageValue(BALANCE_A, abi.Uint64()),
        BALANCE_B: LocalStorageValue(BALANCE_B, abi.Uint64()),
        ORDERS: LocalStorageValue(ORDERS, abi.make(abi.DynamicArray[abi.Uint64])),
    }

    @Subroutine(TealType.uint64)
    def increase_sequence(self):
        return Seq(
            (s := ScratchVar()).store(self.Global[SEQUENCE].get()),
            self.Global[SEQUENCE].set(s.load() + Int(1)),
            s.load()
        )


vex = Vex()


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
