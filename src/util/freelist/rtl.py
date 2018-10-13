from pymtl import *
from bitutil import clog2


class FreeList(Model):
    def __init__(s, nslots):

        nbits = clog2(nslots)
        s.alloc_enable = InPort(1)
        s.alloc_full = OutPort(1)
        s.alloc_output = OutPort(nbits)

        s.free_enable = InPort(1)
        s.free_slot = InPort(nbits)

        ncount_bits = clog2(nslots + 1)
        s.size = Wire(ncount_bits)
        s.full = Wire(1)
        s.free = [Wire(nbits) for _ in range(nslots)]
        s.head = Wire(nbits)
        s.tail = Wire(nbits)

        s.connect(s.full, s.alloc_full)

        for x in range(len(s.free)):

            @s.tick_rtl
            def reset_free():
                if s.reset:
                    s.free[x].next = x

        @s.tick_rtl
        def tick():
            if s.reset:
                s.head.next = 0
                s.tail.next = 0
                s.size.next = 0
            else:
                # If there is an alloc request are we aren't full then we have
                # served it, so advance the head
                if s.alloc_enable and not s.full:
                    s.size.next = s.size.value + 1
                    if s.head.value == nslots - 1:
                        s.head.next = 0
                    else:
                        s.head.next = s.head.value + 1

                # If there is a free request then execute it
                # Note we do not combinationally handle a free request
                # and an alloc request in the same cycle when full
                if s.free_enable:
                    s.free[s.tail.value].next = s.free_slot
                    s.size.next = s.size.value - 1
                    if s.tail.value == nslots - 1:
                        s.tail.next = 0
                    else:
                        s.tail.next = s.tail.value + 1

        @s.combinational
        def b1():
            s.alloc_output.value = s.free[s.head]
            s.full.value = (s.size == nslots)

    def line_trace(s):
        return "hd:{}tl:{}:sz:{}".format(s.head, s.tail, s.size)
