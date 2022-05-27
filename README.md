VEX - Value Exchange
---

On chain order book with using price/time order matching

Each pair of assets (A/B) has an associated Order Book containing resting Limit Orders for each side (Bid/Ask). 

Some metadata for the current state of the book (current bid/ask, midprice, sequence, ...) are also tracked.

Assets for a users resting orders are held in single escrow.

Each side of the order book is implemented as a priority queue, sorted by price and time (sequence).

The ratio between assets is limited to N decimals. 

The distance to the mid price is limited to N ticks. 

This design should:
- Allow Market Orders (Filled by popping from front of queue) 
- Allow Limit Orders (Prices limited in tick size, Filled in order of price/time)
- Allow Order Cancelling/Modification (User holds ref to order and submits cancel for it)