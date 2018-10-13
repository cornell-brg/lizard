from pymtl import *
from bitutil import clog2


class FreeListFL(model):
    def __init__(self, nslots):

        self.nbits = clog2(nslots)
        self.free = [Bits(self.nbits) for _ in range(nslots)]

        ncount_bits = clog2(nslots + 1)
        self.size = Bits(ncount_bits)
        self.head = Bits(nbits)
        self.tail = Bits(nbits)

    def reset(s):
        for x in range(len(self.free)):
            self.free[x] = x

        self.head.next = 0
        self.tail.next = 0
        self.size.next = 0

    def wrap_incr(self, x):
        if x == len(self.free) - 1:
            return 0
        else:
            return x + 1

    # Returns either the tag or None if full
    def alloc():
        if self.size == len(self.free):
            return None
        ret = self.head
        self.size += 1
        self.head = wrap_incr(self.head)
        return ret

    def free(tag):
        self.free[self.tail] = tag
        self.size -= 1
        self.tail = wrap_incr(self.tail)

    def line_trace(s):
        return "hd:{}tl:{}:sz:{}".format(self.head, self.tail, self.size)
