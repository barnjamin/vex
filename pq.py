from typing import List, Tuple
import random

class Order:
    price: int
    size: int
    priority: int

    def __init__(self, price: int, size: int, priority: int):
        self.price=price
        self.priority=priority
        self.size = size

    def key(self):
        return f"{self.price:03}.{self.priority:03}" 

    def __str__(self)->str:
        return f"{self.size}@{self.key()}"

def parent_idx(i: int)->int:
    if i%2 == 0:
        return int((i-1)/2)
    return int(i/2)

def child_idx(i: int)->Tuple[int, int]:
    return i*2, i*2+1

class PriorityQueue:

    def __init__(self):
        self.data: List[Order] = []

    def is_empty(self):
        return len(self.data)==0

    def insert(self, element: Order):

        #Add the element to the bottom level of the heap at the leftmost open space.
        self.data.append(element)

        idx = len(self.data) - 1

        #Compare the added element with its parent; if they are in the correct order, stop.
        while True:
            pidx = parent_idx(idx)
            if self.data[idx].key() < self.data[pidx].key():
                self.swap(idx, pidx)
                idx, pidx = pidx, parent_idx(pidx)
            else:
                break

    def swap(self, i:int, j:int):
        self.data[i], self.data[j] = self.data[j], self.data[i]

    def search(self, element: Order):
        for idx, order in enumerate(self.data):
            if order.key() == element.key():
                return idx

    def remove(self, idx: int):
        #Swap this element with the last element
        self.swap(idx, len(self.data)-1)
        self.data.pop()

        # down-heapify to restore heap property
        while True:
            largest = idx
            lidx, ridx = child_idx(idx)
            if lidx<len(self.data) and self.data[largest].key() > self.data[lidx].key():
                largest = lidx

            if ridx<len(self.data) and self.data[largest].key() > self.data[ridx].key():
                largest = ridx

            if largest != idx:
                self.swap(idx, largest)
                idx = largest 
            else:
                break

    def delete(self, element: Order):
        idx = self.search(element)
        self.remove(idx)

    def peek(self)->Order:
        return self.data[0]

    def pop(self):
        popped = self.data[0]
        self.remove(0)
        return popped

    def update_size(self, new_size):
        self.data[0].size = new_size


pq = PriorityQueue()

book_size = 1000
min_price, max_price = 5, 100

for x in range(book_size):
    o = Order(random.randint(min_price,max_price), random.randint(10, 100), x)
    pq.insert(o)

# Fill order
order = Order(12, 500, 0)
filled = []
while order.size>0:
    resting_order = pq.peek()

    # If the price is good, fill it
    if resting_order.price<=order.price:
        # Partial fill of resting order
        if resting_order.size > order.size:
            pq.update_size(resting_order.size - order.size)
            resting_order.size = order.size
            filled.append(resting_order)
            order.size = 0
        # We've fully filled the resting order
        else:
            filled.append(pq.pop())
            order.size -= resting_order.size

    # We filled as much as we could at this price
    else:
        print("Next order is  "+str(resting_order))
        order.size = 0

print(f"Filled {sum([f.size for f in filled])}")
print([str(f) for f in filled])