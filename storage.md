Sparse Array Storage:
    T: Known Type
    N: Known size of T  `abi.size_of(T)`
    MaxElems: Max elements per Box `floor(floor(MAX_BOX/N)/8)*8`. So we can use a `byte[]` for indicies 

    Page: Box holding data elements
    Index: reletive position in each page
    Slot: Absolute position `[Page, Index]`

    Slots Box: Contains Array of Bitmaps
        - Each Bitmap is represents single page of storage 
        - BitMap: bit[MaxElems], 0 for filled, 1 for free (use bitlen to find first open index)

    Page: T[MaxElems] 

    put(T):
        slot = Find first open slot (iterate over page bitmaps, bitlen for first index, should prefer lower index boxes && indicies)
        mark_occupied(slot)
        [page, index] = slot
        BoxReplace(page, index*N, T.encode()) into page/index
        return slot

    update(slot, T):
        [page, index] = slot
        BoxReplace(page, index*N, T.encode())

    read(slot):
        [page, index] = slot 
        T.decode(BoxExtract(page, index*N, (index+1)*N))

    delete(slot):
        mark_unoccupied(slot)


    Tracking interesting slots is up to the application

    ex:
        FIFO queue as double linked list to allow deletion, head/tail and higher/lower pointers are slots to elements





############################


Is it reasonable to set a max number of elements per Price Queue ? 
Is it reasonable to set a min size of order? max decimals?


Per Box 2500
Per Byte 400


Limits
    Max 8 Boxes per app call (?)
    All Boxes to be accessed must be specified from off chain txn 



Boxes for:
    Order Queue Per Side
        head/tail * 4000
        note: 
            at 2 decimals, this is 40 whole units from mid
            at 3 decimals, this is 4 whole units
            at 4 decimals, this is 0.4
            ...
            Adjust min order size to keep decimals in a reasonable ratio


Each OrderQueue Page:
    order[256]
