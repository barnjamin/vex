from typing import List
from pyteal import *
from application import *
from models import *
from priority_queue import PriorityQueue

kb = 2 ** 10
box_size = Int(32 * kb)

ask_pq = PriorityQueue("ask_book", box_size, Int(1), RestingOrderType)
bid_pq = PriorityQueue("bid_book", box_size, Int(0), RestingOrderType)


class AccountStorage:
    def __init__(self, box_name, type: abi.BaseType):
        self.box_name = box_name
        self.type = type
        self.ts = Int(abi.size_of(type.type_spec()))

    def get(self, idx: Int):
        return BoxExtract(self.box_name, idx * self.ts, self.ts)

    def append(self, type: abi.BaseType) -> abi.Uint64:
        pass


# vet = VexAccount().get_type()
# accts = AccountStorage("accts", vet)


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
        # If theres nothing in the book or empty size, dip
        If(Or(bid_pq.count() == Int(0), size == Int(0)), Return(size)),
        # Peek the book and try to fill
        (ro := RestingOrder()).decode(bid_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        # Next order not fillable
        If(resting_price.get() < price, Return(size)),
        If(
            # Is it a full or partial of resting
            resting_size.get() <= size,
            Seq(
                # Full fill of resting
                bid_pq.remove(Int(0)),
                try_fill_bids(price, size - resting_size.get()),
            ),
            Seq(
                # Partial fill of resting
                (seq := abi.Uint64()).set(ro.sequence()),
                (new_size := abi.Uint64()).set(resting_size.get() - size),
                ro.set(resting_price, seq, new_size),
                # Update resting with new size
                bid_pq.update(Int(0), ro),
                # Return 0 for size left fo fill
                Int(0),
            ),
        ),
    )


@Subroutine(TealType.uint64)
def try_fill_asks(price: Expr, size: Expr):
    return Seq(
        # If theres nothing in the book or empty size, dip
        If(Or(ask_pq.count() == Int(0), size == Int(0)), Return(size)),
        # Peek the book and try to fill
        (ro := RestingOrder()).decode(ask_pq.peek()),
        (resting_price := abi.Uint64()).set(ro.price()),
        (resting_size := abi.Uint64()).set(ro.size()),
        # Next order not fillable
        If(resting_price.get() > price, Return(size)),
        If(
            # Is it a full or partial of resting
            resting_size.get() <= size,
            Seq(
                # Full fill of resting
                ask_pq.remove(Int(0)),
                try_fill_asks(price, size - resting_size.get()),
            ),
            Seq(
                # Partial fill of resting
                (seq := abi.Uint64()).set(ro.sequence()),
                (new_size := abi.Uint64()).set(resting_size.get() - size),
                ro.set(resting_price, seq, new_size),
                # Update resting with new size
                ask_pq.update(Int(0), ro),
                # Return 0 for size left fo fill
                Int(0),
            ),
        ),
    )


class Vex(Application):
    globals: List[GlobalStorageValue] = [
        # Static Config
        GlobalStorageValue("asset_a", TealType.uint64, protected=True),
        GlobalStorageValue("asset_b", TealType.uint64, protected=True),
        GlobalStorageValue("lot_a", TealType.uint64, protected=True),
        GlobalStorageValue("lot_b", TealType.uint64, protected=True),
        GlobalStorageValue("decimals", TealType.uint64, protected=True),
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

# Routable methods
@vex.router.method
def bootstrap():
    return Seq(vex.initialize_globals(), ask_pq.initialize(), bid_pq.initialize())

@vex.router.method
def new_order(
    bid: abi.Bool, price: abi.Uint64, size: abi.Uint64, *, output: abi.Uint64
):
    return Seq(
        (remaining_size := abi.Uint64()).set(size.get()),
        If(
            bid.get(),
            Seq(
                remaining_size.set(try_fill_bids(price.get(), size.get())),
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
            Seq(
                remaining_size.set(try_fill_asks(price.get(), size.get())),
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
        ),
        output.set(size.get() - remaining_size.get()),
    )

#@vex.router.method
#def cancel_order(price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64):
#    pass
#
#@vex.router.method
#def modify_order(price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64, new_size: abi.Uint64):
#    pass

#@vex.router.method
#def register(acct: abi.Account, asset_a: abi.Asset, asset_b: abi.Asset):
#    pass
#