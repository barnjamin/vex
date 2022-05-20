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


Reset seq/priority on move toward mid and increase size


Allow BATCH operations