from pyteal import *
from application import *

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

