from pyteal import Assert, Expr, If, Int, Or, Return, Seq, TealType, abi, Reject
from priority_queue import PriorityQueue, SortOrderGT, SortOrderLT
from beaker import (
    AccountStateValue,
    Application,
    ApplicationStateValue,
    external,
    internal,
)

MAX_BOX_SIZE = 1024 * 4


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

    # DO NOT CHANGE THE ORDER
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

    # Config
    asset_a = ApplicationStateValue(TealType.uint64, static=True)
    asset_b = ApplicationStateValue(TealType.uint64, static=True)
    min_lot_a = ApplicationStateValue(TealType.uint64, static=True)
    min_lot_b = ApplicationStateValue(TealType.uint64, static=True)
    max_decimals = ApplicationStateValue(TealType.uint64, static=True)

    # Updated
    seq = ApplicationStateValue(TealType.uint64)
    bid = ApplicationStateValue(TealType.uint64)
    ask = ApplicationStateValue(TealType.uint64)
    mid = ApplicationStateValue(TealType.uint64)

    box_size = Int(MAX_BOX_SIZE)

    ask_queue = PriorityQueue("ask_book", box_size, SortOrderLT, RestingOrder)
    bid_queue = PriorityQueue("bid_book", box_size, SortOrderGT, RestingOrder)

    # TODO: no
    ask_counter = ask_queue.counter
    bid_counter = bid_queue.counter

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
        return Assert(self.ask_queue.initialize(), self.bid_queue.initialize())

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
            .Then( # Check to see if we can fill any asks
                size.set(self.fill_asks(price.get(), size.get())),
                If(size.get()).Then( # Still have size, put in the queue
                    self.add_bid(
                        price,
                        size,
                        Seq(self.seq.increment(), self.seq),
                    ),
                ),
            )
            .Else( # Check to see if we can fill any bids
                size.set(self.fill_bids(price.get(), size.get())),
                If(size.get()).Then( # Still have size, put it in the queue
                    self.add_ask(
                        price,
                        size,
                        Seq(self.seq.increment(), self.seq),
                    )
                ),
            ),
            output.set(output.get() - size.get()),
            # Update bid/mid/ask
            self.update_stats()
        )

    @external
    def cancel_order(
        self, price: abi.Uint64, seq: abi.Uint64, size: abi.Uint64, acct_id: abi.Uint64
    ):
        return Reject() 

    @external
    def modify_order(
        self,
        price: abi.Uint64,
        seq: abi.Uint64,
        size: abi.Uint64,
        acct_id: abi.Uint64,
        new_size: abi.Uint64,
    ):
        return Reject() 

    @external
    def register(self, acct: abi.Account, asset_a: abi.Asset, asset_b: abi.Asset):
        # Add a new member to the member list, assigning them a 
        # sequence id that we can access
        return Reject()

    @internal(TealType.none)
    def update_stats(self):
        return Seq(
            If(self.ask_queue.count() > Int(0)).Then(
                (ro := RestingOrder()).decode(self.ask_queue.peek()),
                (resting_price := abi.Uint64()).set(ro.price),
                self.ask.set(resting_price.get()),
            ),
            If(self.bid_queue.count() > Int(0)).Then(
                # Peek the book and try to fill
                (ro := RestingOrder()).decode(self.bid_queue.peek()),
                (resting_price := abi.Uint64()).set(ro.price),
                self.bid.set(resting_price.get()),
            ),
            If(self.ask > self.bid).Then(
                self.mid.set(self.bid + ((self.ask - self.bid) / Int(2))),
            )
        )

    @internal(TealType.none)
    def add_bid(self, price: abi.Uint64, size: abi.Uint64, seq: Expr):
        return Seq(
            (s := abi.Uint64()).set(seq),
            (resting_order := RestingOrder()).set(price, s, size),
            self.bid_queue.insert(resting_order),
        )

    @internal(TealType.none)
    def add_ask(self, price: abi.Uint64, size: abi.Uint64, seq: Expr):
        return Seq(
            (s := abi.Uint64()).set(seq),
            (resting_order := RestingOrder()).set(price, s, size),
            self.ask_queue.insert(resting_order),
        )

    @internal(TealType.uint64)
    def fill_bids(self, price: Expr, size: Expr):
        return Seq(
            # If theres nothing in the book or empty size, dip
            If(Or(self.bid_queue.count() == Int(0), size == Int(0)), Return(size)),
            # Peek the book and try to fill
            (ro := RestingOrder()).decode(self.bid_queue.peek()),
            (resting_price := abi.Uint64()).set(ro.price),
            (resting_size := abi.Uint64()).set(ro.size),
            # Next order not fillable
            If(resting_price.get() < price, Return(size)),
            If(
                resting_size.get() <= size,
                Seq( # Full fill of resting
                    self.bid_queue.remove(Int(0)),
                    # Check the next one after subtracting filled portion
                    self.fill_bids(price, size - resting_size.get()),
                ),
                Seq( # Partial fill of resting
                    (seq := abi.Uint64()).set(ro.sequence),
                    (new_size := abi.Uint64()).set(resting_size.get() - size),
                    ro.set(resting_price, seq, new_size),
                    # Update resting with new size
                    self.bid_queue.update(Int(0), ro),
                    # Return 0 for size left fo fill
                    Int(0),
                ),
            ),
        )

    @internal(TealType.uint64)
    def fill_asks(self, price: Expr, size: Expr):
        return Seq(
            # If theres nothing in the book or empty size, dip
            If(Or(self.ask_queue.count() == Int(0), size == Int(0)), Return(size)),
            # Peek the book and try to fill
            (ro := RestingOrder()).decode(self.ask_queue.peek()),
            (resting_price := abi.Uint64()).set(ro.price),
            (resting_size := abi.Uint64()).set(ro.size),
            # Next order not fillable
            If(resting_price.get() > price, Return(size)),
            If(
                # Is it a full or partial of resting
                resting_size.get() <= size,
                Seq(
                    # Full fill of resting
                    self.ask_queue.remove(Int(0)),
                    # Check the next one after subtracting filled portion
                    self.fill_asks(price, size - resting_size.get()),
                ),
                Seq(
                    # Partial fill of resting
                    (seq := abi.Uint64()).set(ro.sequence),
                    (new_size := abi.Uint64()).set(resting_size.get() - size),
                    ro.set(resting_price, seq, new_size),
                    # Update resting with new size
                    self.ask_queue.update(Int(0), ro),
                    # Return 0 for size left fo fill
                    Int(0),
                ),
            ),
        )


if __name__ == "__main__":
    Vex().dump("./artifacts")
