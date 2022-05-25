Sparse Array Storage T[]:

    T: Known Type
    N: Known size of T  `abi.size_of(T)`
    MaxElems: Max elements per Box `floor(floor(MAX_BOX/N)/8)*8`. So we can use a `byte[]` for indicies 

    Page: Box holding data elements `T[MaxElems]`
    Index: reletive position in each page
    Slot: Absolute position `[Page, Index]`

    Table Of Contents: Contains Array of Bitmaps
        - Each Bitmap is represents single page of storage 
        - BitMap: bit[MaxElems], 0 for filled, 1 for free (use bitlen to find first open index)

    put(T):
        slot = Find first open slot (iterate over page bitmaps, bitlen for first index, should prefer lower index boxes && indicies)
        mark_occupied(slot)
        update(slot, T)

    get(slot):
        [page, index] = slot 
        T.decode(BoxExtract(page, index*N, (index+1)*N))

    update(slot, T):
        [page, index] = slot
        BoxReplace(page, index*N, T.encode())

    delete(slot):
        mark_unoccupied(slot)


Tracking interesting slots is up to the application

Alloc/Dealloc should be private methods that allow for new Box creation/deletion as needed 

ex:
    FIFO queue as double linked list to allow deletion, head/tail and higher/lower pointers are slots to elements


# Oder Book

Each side of the book contains some N orders, each filled according to price/time

BidSide = [
    10.01: [{}, {}, {}],
    10.02: [],
    10.03: [{}, {}, {}, {}, {}, {}],
    ...
]

Orders are filled by price from mid price out. Within each price, orders are filled from first order placed to last as in a Priority Queue. 

Each order is appended to the Priority Queue that represents the list of orders at that price by updating pointers in the previous/next entries to reference the new order.

Each order is stored to the first open slot, which may be _any_ box with free space.

An Order can be modified in place by having its size changed.
An Order can be filled or cancelled by marking the slot as empty and updating pointers in adjacent entries.

## Challange

Because we may specify a max 8 Boxes per app call and all Boxes to be accessed must be specified from off chain, we need to 
be able to determine _which_ boxes should be requested in the case of an incoming order.

Ideally, the entire contiguous list of orders to fill are accessible in a single transaction.

If we naively place orders in any available slots, a single price's priority queue may have its orders scattered across N>8 Boxes.

    At 64b/order and 16kb/box we can store 256 orders per box. With 8 Boxes of access we may access up to 2048 orders in a single application call. 
    But out of those 2048, there is no guarantee that these orders are the ones that _should_ be filled next according to price/time priority.

How can we keep both priority queue elements and sequential priority queues in order on disk?