XEV - eXchange Expected Value
---

On chain order book with order price time order matching

Each pair of assets (X/Y) has an associated Order Book containing resting Limit Orders for each side (Bid/Ask). Some metadata for the current state of the book (total volume, midprice, ...) are also tracked.

Assets for a users resting orders are held in escrow.

Each side of the order book is implemented as a doubly linked list representing a queue of orders, sorted by price and time.

The ratio between assets is limited to N decimals. The distance to the mid price is limited to N ticks. 

Each PriceOrderBook is stored in its own box, keyed by price.

It should be possible to know off chain what set of boxes you'll need to request.

This design should:
- Allow Market Orders (Filled by popping from front of queue) 
- Allow Limit Orders (Prices limited in tick size, Filled in order of price/time)
- Allow Order Cancelling/Modification (User holds ref to order and submits cancel for it)

## Structures

```py
class IncomingOrder():
    BidSide : abi.Boolean 
    Price   : abi.Uint64
    Size    : abi.Uint64
    Address : abi.Address
```

```py
class RestingOrder():
    Address  : abi.Address
    Amount   : abi.Uint64 
    Priority : abi.Uint64
    Prev     : abi.Uint16
    Next     : abi.Uint16
```

```py
class OrderBook():
    Midprice : abi.Uint64
    Decimals : abi.Uint8
    AskPrice : abi.Uint64 
    BidPrice : abi.Uint64

    def get_price_order_book(self, Price):
        pass

    def get_next_price(self, Price):
        # Find the key for the next PriceOrderBook given incoming price
        pass

    def price_match(self, IncomingOrder):
        if IncomingOrder.Side == Bid:
            return IncomingOrder.Price>=self.AskPrice
        return IncomingOrder.Price<=self.BidPrice


    def handle_incoming_order(self, IncomingOrder):
        if self.price_match(IncomingOrder.max_price):
            self.fill_order(IncomingOrder)
        else: 
            self.add_new_order(IncomingOrder)

    def add_new_order(self, IncomingOrder):
        PriceOrderBook = self.get_price_order_book(IncomingOrder.Price)
        PriceOrderBook.push_new_order(IncomingOrder)

    def fill_order(self, IncomingOrder):
        PriceOrderBook = OrderBook.get_price_order_book(IncomingOrder.Price)

        while !IncomingOrder.filled():

            # We reached the end of this PriceOrderBook 
            if PriceOrderBook.Highest == 0:
                # Check in the next price
                next_price = OrderBook.get_next_price(Incoming.Price)
                if next_price != 0:
                    # We've got another PriceOrderBook to check
                    OrderBook.set_next_price(next_price)
                    IncomingOrder.Price = next_price
                    return OrderBook.handle_incoming_order(IncomingOrder)
                else:
                    # Side depleted, we're all out of resting orders, just create a new resting order 
                    return PriceOrderBook.push_new_order(IncomingOrder)

            RestingOrder = PriceOrderBook.read(PriceOrderBook.Highest)

            itxn_fill(Order, Price, Size, Addr)

            PriceOrderBook.mark_free(PriceOrderBook.Highest)
            PriceOrderBook.Highest = CurrentOrder.Lower
            PriceOrderBook.write(PriceOrderBook.Highest, {
                Highest: 0,
            })

    def cancel_order(OrderCancel):
        Assert(Order.Address == Address)

        PriceOrderBook = self.get_price_order_book(OrderCancel.Price)
        slot = PriceOrderBook.lookup(OrderCancel.Priority, OrderCancel.Address)

        RestingOrder = PriceOrderBook.read(slot)

        PriceOrderBook.mark_empty(slot)
        PriceOrderBook.write(RestingOrder.Higher {
            Lower: RestingOrder.Lower,
        })
        PriceOrderBook.write(RestingOrder.Lower, {
            Higher: RestingOrder.Higher
        })

    def change_volume(self, OrderModifySize):
        PriceOrderBook = self.get_price_order_book(OrderModifySize.Price)
        slot = PriceOrderBook.lookup(OrderModifySize.Priority, OrderModifySize.Address)
        PriceOrderBook.write(slot, {
            Size: OrderModifySize.Size
        })
```

```py
class PriceOrderBook():
    MinSize: abi.Uint64
    # Each empty slot in our Order book is listed here
    OpenSlots:  abi.DynamicArray[abi.Uint16]
    # Current priority sequence value
    Priority:    abi.Uint64
    # How many orders are resting
    NumOrders:   abi.Uint16
    # Top of queue
    Highest:    abi.Uint16
    # Bottom of queue
    Lowest:     abi.Uint16
    # Mid of queue for faster searches?
    Mid:   abi.Uint16
    # Virtual field?
    Queue: abi.DynamicArray[RestingLimitOrder]

    def push_new_order(Price, Size, Address):
        PriceOrderBook = OrderBook.get_price_order_book(Price)

        slot = PriceOrderBook.next_slot()

        PriceOrderBook.write(PriceOrderBook.Lowest, {
            Lower: slot
        })

        PriceOrderBook.write(slot, {
            Higher: PriceOrderBook.Lowest, 
            Address: Address, 
            Size: Size, 
            Priority: PriceOrderBook.increment_sequence()
        })