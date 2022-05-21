Per Box 2500
Per Byte 400






Limits
    Max 8 Boxes per app call
    All Boxes must be specified ahead of time

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
