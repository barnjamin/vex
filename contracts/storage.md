VEX Order Book
==============

The VEX order book for a given side (bid/ask) is implemented as a set of lists of orders.

Each list contains all orders at a given price.

Lists are stored immediately adjacent in 4k boxes. The boxes _may_ have slack space at the end.

!! Note: 

    We're essentially trying to manage pages of memory, termed boxes and efficiently allocate new boxes/coalesce adjacent boxes 


## Layout

```
       MidPrice is 10.00

       Resting Ask Limit Orders
      ┌─────────────────────────────────────────────────────────────┐
      │                                                             │
      │                                                             │
      │    Box 0000  Summary: 10.01=>10.06, 34 orders, 400 units    │
      │   ┌───────────────┬────────┬──────────────────────┬─────┐   │
      │   │15 orders      │7       │22 @ 10.05            │     │   │
      │   │@ 10.01        │@ 10.02 │                      │     │   │
      │   │               │        │                      │ xxx │   │
      │   │               │        │                      │     │   │
      │   │               │        │                      │     │   │
      │   │               │        │                      │     │   │
      │   └───────────────┴────────┴──────────────────────┴─────┘   │
      │    Box 0001                                                 │
      │   ┌───────────┬─────────┬┬───────┬───┬────┬──┬──────────┐   │
      │   │           │         ││       │   │    │  │          │   │
      │   │           │         ││       │   │    │  │          │   │
      │   │           │         ││       │   │    │  │ xxxxxxx  │   │
      │   │           │         ││       │   │    │  │          │   │
      │   │           │         ││       │   │    │  │          │   │
      │   │           │         ││       │   │    │  │          │   │
      │   └───────────┴─────────┴┴───────┴───┴────┴──┴──────────┘   │
      │                                                             │
      │                             │                               │
      │                             │                               │
      │                             │                               │
      │                             │                               │
      │                             │                               │
      │                             │                               │
      │                             ▼                               │
      │                                                             │
      └─────────────────────────────────────────────────────────────┘
```

## fill order

As orders are filled, we remove them from the boxes holding them and slide the remaining orders in the box to the left.  Empty boxes are deleted.

```
┌─────────────────────────┬────────┬─────────────────┬────────────┐
│                         │        │                 │            │
│                         │        │                 │            │
│                         │        │                 │            │
│                         │        │                 │  xxxxxxx   │
│                         │        │                 │            │
│                         │        │                 │            │
│                         │        │                 │            │
└─────────────────────────┴───┬────┴─────────────────┴────────────┘
                              │
                              │
                              |
                              ▼
┌────────────────┬────────┬────────┬─────────────────┬────────────┐
│                │        │        │                 │            │
│ xxxxxxxxxxx    │        │        │                 │            │
│                │        │        │                 │            │
│ Filled         │        │        │                 │  xxxxxxx   │
│                │        │        │                 │            │
│ xxxxxxxxxxx    │        │        │                 │            │
│                │        │        │                 │            │
└────────────────┴────────┴───┬────┴─────────────────┴────────────┘
                              │
                              │
                              ▼
┌────────┬────────┬─────────────────┬─────────────────────────────┐
│        │        │                 │                             │
│        │        │                 │                             │
│        │        │                 │                             │
│        │        │                 │  xxxxxxxxxxxxxxxxxxxxxxxxx  │
│        │        │                 │                             │
│        │        │                 │                             │
│        │        │                 │                             │
└────────┴────────┴─────────────────┴─────────────────────────────┘

```



## new order

As new orders come in, we slide the orders at price increments after the orders price to the right. 

If the slide would result in breaching the box boundary, we first check the next box (if we have access) to see if we can move the entire list into it, otherwise we create a new box containing it. NOTE this requires the new boxes name be passed as a reference



```
   EX 1. New order, plenty of space in the existing box

    new order─────────────┐
                          ▼
   ┌──────────────────────┬───────┬─────────────────────┐
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │  xxxxxxxxxxxxxxxxx  │
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │                     │
   └──────────────────────┴───────┴─────────────────────┘

   ┌────────────────────────┬───────┬───────────────────┐
   │                        │       │                   │
   │                        │       │                   │
   │                        │       │  xxxxxxxxxxxxxxxx │
   │                        │       │                   │
   │                        │       │                   │
   │                        │       │                   │
   └────────────────────────┴───────┴───────────────────┘

```

```
   EX 2. New order, box already full 

    new order─────────────┐
                          ▼
   ┌──────────────────────┬───────┬─────────────────────┐
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │                     │
   │                      │       │                     │
   └──────────────────────┴───────┴─────────────────────┘

Becomes

   ┌────────────────────────┬───────┬────────────────────┐
   │                        │       │                    │
   │                        │       │                    │
   │                        │       │  xxxxxxxxxxxxxxxx  │
   │                        │       │                    │
   │                        │       │                    │
   │                        │       │                    │
   └────────────────────────┴───────┴────────────────────┘

   ┌─────────────────────┬────────────────────────────────┐
   │                     │                                │
   │                     │                                │
   │                     │       xxxxxxxxxxxxxxxx         │
   │                     │                                │
   │                     │                                │
   │                     │                                │
   └─────────────────────┴────────────────────────────────┘



```

# cancel order

As orders are cancelled, we remove it from the box holding it and slide remaining orders in the box to the left. Empty boxes are deleted.
