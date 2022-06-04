from venv import create
from pyteal import *
from application import *
from models import *
import bookkeeping

vex = Application(
    [
        # Static Config
        GlobalStorageValue("asset_a", TealType.uint64, protected=True),
        GlobalStorageValue("asset_b", TealType.uint64, protected=True),
        GlobalStorageValue("min_lot_a", TealType.uint64, protected=True),
        GlobalStorageValue("min_lot_b", TealType.uint64, protected=True),
        GlobalStorageValue("max_decimals", TealType.uint64, protected=True),
        # Updated as needed
        GlobalStorageValue("seq", TealType.uint64),
        GlobalStorageValue("bid", TealType.uint64),
        GlobalStorageValue("ask", TealType.uint64),
        GlobalStorageValue("mid", TealType.uint64),
        # Box storage counters
        bookkeeping.ask_pq.counter,
        bookkeeping.bid_pq.counter,
    ],
    [
        # Amount avail to withdraw
        LocalStorageValue("avail_bal_a", TealType.uint64),
        LocalStorageValue("avail_bal_b", TealType.uint64),
        # Amount reserved on pending order
        LocalStorageValue("reserved_bal_a", TealType.uint64),
        LocalStorageValue("reserved_bal_b", TealType.uint64),
        # Sequences of orders
        LocalStorageValue("orders", TealType.bytes),
    ],
    Router(
        "vex",
        BareCallActions(
            no_op=OnCompleteAction.create_only(Approve()),
            update_application=OnCompleteAction.always(
                Return(Txn.sender() == Global.creator_address())
            ),
            delete_application=OnCompleteAction.always(
                Return(Txn.sender() == Global.creator_address())
            ),
            opt_in=OnCompleteAction.always(Approve()),
            clear_state=OnCompleteAction.always(Approve()),
            close_out=OnCompleteAction.always(Approve()),
        ),
    ),
)


# Routable methods
@vex.router.method
def bootstrap():
    """ Bootstraps the global variables and boxes """
    return Seq(
        vex.initialize_globals(),
        bookkeeping.ask_pq.initialize(),
        bookkeeping.bid_pq.initialize(),
    )


@vex.router.method
def new_order(
    is_bid: abi.Bool, price: abi.Uint64, size: abi.Uint64, *, output: abi.Uint64
):
    """
        Accepts a new order and tries to fill it
        if unfillable, place it in the queue 
    """
    return Seq(
        (remaining_size := abi.Uint64()).set(size.get()),
        If(
            is_bid.get(),
            Seq(
                remaining_size.set(bookkeeping.try_fill_bids(price.get(), size.get())),
                If(
                    remaining_size.get() > Int(0),
                    bookkeeping.add_ask(
                        price,
                        remaining_size,
                        vex.globals["seq"].increment(),
                    ),
                ),
            ),
            Seq(
                remaining_size.set(bookkeeping.try_fill_asks(price.get(), size.get())),
                If(
                    remaining_size.get() > Int(0),
                    bookkeeping.add_bid(
                        price,
                        remaining_size,
                        vex.globals["seq"].increment(),
                    ),
                ),
            ),
        ),
        output.set(size.get() - remaining_size.get()),
    )


# @vex.router.method
# def cancel_order(price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64):
#    pass
#
# @vex.router.method
# def modify_order(price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64, new_size: abi.Uint64):
#    pass

# @vex.router.method
# def register(acct: abi.Account, asset_a: abi.Asset, asset_b: abi.Asset):
#    pass
#
