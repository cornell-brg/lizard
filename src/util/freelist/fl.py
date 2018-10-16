from pymtl import *
from bitutil import clog2


class FreeListFL(Model):
    def __init__(self, nslots):

        self.nbits = clog2(nslots)
        self.free_list = [Bits(self.nbits) for _ in range(nslots)]

        ncount_bits = clog2(nslots + 1)
        self.size = Bits(ncount_bits)
        self.head = Bits(self.nbits)
        self.tail = Bits(self.nbits)

    def fl_reset(self):
        for x in range(len(self.free_list)):
            self.free_list[x] = x

        self.head= 0
        self.tail= 0
        self.size= 0

    def wrap_incr(self, x):
        if x == len(self.free_list) - 1:
            return 0
        else:
            return x + 1

    # Returns either the tag or None if full
    def alloc(self):
        if self.size == len(self.free_list):
            return None
        ret = self.head
        self.size += 1
        self.head = self.wrap_incr(self.head)
        return ret

    def free(self, tag):
        self.free_list[self.tail] = tag
        self.size -= 1
        self.tail = self.wrap_incr(self.tail)

    def line_trace(self):
        return "hd:{}tl:{}:sz:{}".format(self.head, self.tail, self.size)
