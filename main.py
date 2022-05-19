from typing import Dict
from pyteal import *

Price = abi.Uint64

class IncomingOrder():
    BidSide : abi.Bool
    Price   : Price 
    Size    : abi.Uint64
    Address : abi.Address

class RestingOrder():
    Address  : abi.Address
    Amount   : abi.Uint64 
    Priority : abi.Uint64
    Prev     : abi.Uint16
    Next     : abi.Uint16

class CancelOrder():
    pass

class ModifyOrderSize():
    pass

class OrderBook():
    Midprice : abi.Uint64
    Decimals : abi.Uint8
    AskPrice : abi.Uint64 
    BidPrice : abi.Uint64

    def get_price_order_book(self, p: Price):
        pass

    def get_next_price(self, p: Price):
        # Find the key for the next PriceOrderBook given incoming price
        pass

    def set_next_price(self, p: Price, BidSide: abi.Bool):
        # Find the key for the next PriceOrderBook given incoming price
        if BidSide:
            self.BidPrice = p
        else:
            self.AskPrice = p

    def price_match(self, io: IncomingOrder):
        if io.BidSide:
            return io.Price>=self.AskPrice
        return io.Price<=self.BidPrice


    def handle_incoming_order(self, io: IncomingOrder):
        if self.price_match(io.Price):
            self.fill_order(io)
        else: 
            self.add_new_order(io)

    def add_new_order(self, io: IncomingOrder):
        PriceOrderBook = self.get_price_order_book(io.Price)
        PriceOrderBook.push_new_order(io)

    def fill_order(self, io: IncomingOrder):
        p_ob: PriceOrderBook = self.get_price_order_book(io.Price)

        while not io.filled():
            # We reached the end of this PriceOrderBook 
            if p_ob.Highest == 0:
                # Check in the next price
                next_price = self.get_next_price(io.Price)
                if next_price != 0:
                    # We've got another PriceOrderBook to check
                    self.set_next_price(next_price)
                    io.Price = next_price
                    return self.handle_incoming_order(io)
                else:
                    # Side depleted, we're all out of resting orders, just create a new resting order 
                    return p_ob.push_new_order(IncomingOrder)

            ro = p_ob.read(p_ob.Highest)

            #itxn_fill(Order, Price, Size, Addr)

            p_ob.mark_free(p_ob.Highest)
            p_ob.Highest = ro.Lower
            p_ob.write(p_ob.Highest, {
                "Highest": 0,
            })

    def cancel_order(self, co: CancelOrder):

        p_ob: PriceOrderBook = self.get_price_order_book(co.Price)
        slot: abi.Uint16 = p_ob.lookup(co.Priority, co.Address)

        ro: RestingOrder = p_ob.read(slot)
        Assert(ro.Address == co.Address)

        p_ob.free_slot(slot)

        p_ob.write(ro.Higher, {
            "Lower": ro.Lower,
        })

        p_ob.write(ro.Lower, {
            "Higher": ro.Higher
        })

    def change_volume(self, mos: ModifyOrderSize):
        PriceOrderBook = self.get_price_order_book(mos.Price)
        slot = PriceOrderBook.lookup(mos.Priority, mos.Address)
        PriceOrderBook.write(slot, {
            "Size": mos.Size
        })

    def push_new_order(self, Price, Size, Address):
        p_ob = self.get_price_order_book(Price)
        slot = p_ob.next_slot()

        self.write(p_ob.Lowest, {
            "Lower": slot
        })

        self.write(p_ob, {
            "Higher": self.Lowest, 
            "Address": Address, 
            "Size": Size, 
            "Priority": self.increment_sequence()
        })

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
    Queue: abi.DynamicArray[RestingOrder]

    def write(slot: abi.Uint16, vals: Dict[str, abi.BaseType]):
        pass

    def read(slot: abi.Uint16)->RestingOrder:
        pass

    def next_slot()->abi.Uint16:
        pass

    def free_slot(slot: abi.Uint16):
        pass

