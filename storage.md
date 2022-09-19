VEX Partitioned Priority Queue
==============================

# Description 

A set of items in a large priority queue is partitioned across Boxes with indexed access.

An Index into the contents of the boxes is kept and consulted by an off-chain client to determine which boxes they may need to access.

IndexItem {
    MaxValue uint64
    MinValue uint64
    BoxName  byte[]
}

Because orders are always taken in a specific sequence we need not maintain an index to the index, the 0th element will represent the first box with data, the 1st will represent the second, and so on.


## Incoming order:

    lookup which queue its in (each should have a max/min value and a pointer to its location)
    place in storage
    if PQ is over some limit:
        pop-scan from top => some threshold (half?)
        box-copy to new sector

## Pop order:

    pop-scan to find orders we'd fill
    fill them
    box-copy to overwrite

## Cancel order:

    remove item
    repair pq 

## Prefill: (read-only)

    request the list of boxes needed
