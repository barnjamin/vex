from pyteal import *
from priority_queue import PriorityQueue
from beaker import *

MAX_BOX_SIZE = 1024
box_size = Int(MAX_BOX_SIZE)


class VexAccount(abi.NamedTuple):
    """Represents an account that has registered with the VEX"""

    address: abi.Field[abi.Address]
    balance_a: abi.Field[abi.Uint64]
    balance_b: abi.Field[abi.Uint64]
    reserved_a: abi.Field[abi.Uint64]
    reserved_b: abi.Field[abi.Uint64]
    credits: abi.Field[abi.Uint64]


class RestingOrder(abi.NamedTuple):
    """Represents a resting limit order"""

    price: abi.Field[abi.Uint64]
    sequence: abi.Field[abi.Uint64]
    size: abi.Field[abi.Uint64]


class IncomingOrderCancel(abi.NamedTuple):
    price: abi.Field[abi.Uint64]
    address: abi.Field[abi.Address]


class IncomingOrderChangeSize(abi.NamedTuple):
    price: abi.Field[abi.Uint64]
    address: abi.Field[abi.Address]
    current_size: abi.Field[abi.Uint64]
    new_size: abi.Field[abi.Uint64]


class Vex(Application):

    asset_a = ApplicationStateValue(TealType.uint64, static=True)
    asset_b = ApplicationStateValue(TealType.uint64, static=True)
    min_lot_a = ApplicationStateValue(TealType.uint64, static=True)
    min_lot_b = ApplicationStateValue(TealType.uint64, static=True)
    max_decimals = ApplicationStateValue(TealType.uint64, static=True)
    seq = ApplicationStateValue(TealType.uint64)
    bid = ApplicationStateValue(TealType.uint64)
    ask = ApplicationStateValue(TealType.uint64)
    mid = ApplicationStateValue(TealType.uint64)

    ask_pq = PriorityQueue("ask_book", box_size, Int(1), RestingOrder().type_spec())
    bid_pq = PriorityQueue("bid_book", box_size, Int(0), RestingOrder().type_spec())

    # TODO: no
    ask_counter = ask_pq.counter
    bid_counter = bid_pq.counter

    # Amount avail to withdraw
    avail_bal_a = AccountStateValue(TealType.uint64)
    avail_bal_b = AccountStateValue(TealType.uint64)
    # Amount reserved on pending order
    reserved_bal_a = AccountStateValue(TealType.uint64)
    reserved_bal_b = AccountStateValue(TealType.uint64)
    # Sequences of orders
    orders = AccountStateValue(TealType.bytes)

    # Routable methods
    @external
    def boostrap(self):
        """Bootstraps the global variables and boxes"""
        return Assert(self.ask_pq.initialize(), self.bid_pq.initialize())

    @external
    def new_order(
        self,
        is_bid: abi.Bool,
        price: abi.Uint64,
        size: abi.Uint64,
        *,
        output: abi.Uint64,
    ):
        """
        Accepts a new order and tries to fill it
        if unfillable, place it in the queue
        """
        return Seq(
            # Copy it now so we can report size filled to caller
            output.set(size),
            If(is_bid.get())
            .Then(
                size.set(self.fill_bids(price.get(), size.get())),
                If(size.get()).Then(
                    self.add_ask(
                        price,
                        size,
                        Seq(self.seq.set(self.seq + Int(1)), self.seq.get()),
                    )
                ),
            )
            .Else(
                size.set(self.fill_asks(price.get(), size.get())),
                If(size.get()).Then(
                    self.add_bid(
                        price,
                        size,
                        Seq(self.seq.set(self.seq + Int(1)), self.seq.get()),
                    ),
                ),
            ),
            output.set(output.get() - size.get()),
        )

    @external
    def cancel_order(
        self, price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64
    ):
        return Assert(Int(0))

    @external
    def modify_order(
        self,
        price: abi.Uint64,
        seq: abi.Uint64,
        size: abi.Uint64,
        acct_id: abi.Uint64,
        new_size: abi.Uint64,
    ):
        return Assert(Int(0))

    @external
    def register(self, acct: abi.Account, asset_a: abi.Asset, asset_b: abi.Asset):
        return Assert(Int(0))

    @internal(TealType.none)
    def add_bid(self, price: abi.Uint64, size: abi.Uint64, seq: Expr):
        return Seq(
            (s := abi.Uint64()).set(seq),
            (resting_order := RestingOrder()).set(price, s, size),
            self.bid_pq.insert(resting_order),
        )

    @internal(TealType.none)
    def add_ask(self, price: abi.Uint64, size: abi.Uint64, seq: Expr):
        return Seq(
            (s := abi.Uint64()).set(seq),
            (resting_order := RestingOrder()).set(price, s, size),
            self.ask_pq.insert(resting_order),
        )

    @internal(TealType.uint64)
    def fill_bids(self, price: Expr, size: Expr):
        return Seq(
            # If theres nothing in the book or empty size, dip
            If(Or(self.bid_pq.count() == Int(0), size == Int(0)), Return(size)),
            # Peek the book and try to fill
            (ro := RestingOrder()).decode(self.bid_pq.peek()),
            (resting_price := abi.Uint64()).set(ro.price),
            (resting_size := abi.Uint64()).set(ro.size),
            # Next order not fillable
            If(resting_price.get() < price, Return(size)),
            If(
                # Is it a full or partial of resting
                resting_size.get() <= size,
                Seq(
                    # Full fill of resting
                    self.bid_pq.remove(Int(0)),
                    # Check the next one after subtracting filled portion
                    self.fill_bids(price, size - resting_size.get()),
                ),
                Seq(
                    # Partial fill of resting
                    (seq := abi.Uint64()).set(ro.sequence),
                    (new_size := abi.Uint64()).set(resting_size.get() - size),
                    ro.set(resting_price, seq, new_size),
                    # Update resting with new size
                    self.bid_pq.update(Int(0), ro),
                    # Return 0 for size left fo fill
                    Int(0),
                ),
            ),
        )

    @internal(TealType.uint64)
    def fill_asks(self, price: Expr, size: Expr):
        return Seq(
            # If theres nothing in the book or empty size, dip
            If(Or(self.ask_pq.count() == Int(0), size == Int(0)), Return(size)),
            # Peek the book and try to fill
            (ro := RestingOrder()).decode(self.ask_pq.peek()),
            (resting_price := abi.Uint64()).set(ro.price),
            (resting_size := abi.Uint64()).set(ro.size),
            # Next order not fillable
            If(resting_price.get() > price, Return(size)),
            If(
                # Is it a full or partial of resting
                resting_size.get() <= size,
                Seq(
                    # Full fill of resting
                    self.ask_pq.remove(Int(0)),
                    # Check the next one after subtracting filled portion
                    self.fill_asks(price, size - resting_size.get()),
                ),
                Seq(
                    # Partial fill of resting
                    (seq := abi.Uint64()).set(ro.sequence),
                    (new_size := abi.Uint64()).set(resting_size.get() - size),
                    ro.set(resting_price, seq, new_size),
                    # Update resting with new size
                    self.ask_pq.update(Int(0), ro),
                    # Return 0 for size left fo fill
                    Int(0),
                ),
            ),
        )
