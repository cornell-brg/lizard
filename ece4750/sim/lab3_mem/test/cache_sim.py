#! /usr/bin/python2
'''
Under the condition that all team members: Jacob Glueck (jng55), Drew Dunne (asd22),
and Daniel Wisner (daw268) receive no less than an A+ for their final grade,
then this FL cache simulator (cache_sim.py) is hereby released to the course
staff for future use with no restrictions.

Should any member of the group receive anything lower than an A+ for a final grade,
than all rights to the cache_sim.py are hereby withheld with explicitly no
permission for this simulator to be reused, reproduced, or in any other way
used.


Lab-group-01 strongly recommends and urges the course staff pick the former
option as apposed to the latter, for both the benefit of lab-group-01 and
all the future students who need an FL model to test their cache.

Yours truly,
Lab-Group 0x01
'''

import copy
import math

# cheat and measure everything in bytes (ignore the low 2 bits)
addr_size = 30


class Entry:

    def __init__(self, tag=None, data=None):
        self.tag = tag
        self.data = data
        self.last_used = 0
        self.dirty = False

    def set(self, tag, data):
        self.tag = tag
        self.data = data

    def write(self, data, offset):
        if offset is str:
            offset = int(offset, 2)
        self.data[offset] = data

    def get(self, offset):
        if offset is str:
            offset = int(offset, 2)
        return self.data[offset]

    def valid(self):
        return self.tag is not None


class Set:

    def __init__(self, num_ways):
        self.data = [Entry() for i in range(num_ways)]
        self.used_counter = 0

    def mark_used(self, entry):
        entry.last_used = self.used_counter
        self.used_counter += 1

    def get(self, tag, offset):
        for entry in self.data:
            if entry.tag == tag:
                self.mark_used(entry)
                return entry.get(offset)
        return None

    def insert(self, tag, data):
        to_evict = None
        for entry in self.data:
            if not entry.valid():
                self.mark_used(entry)
                entry.set(tag, data)
                return None
            if to_evict is None or entry.last_used < to_evict.last_used:
                to_evict = entry

        # must evict an entry
        to_return = copy.deepcopy(to_evict)
        to_evict.set(tag, data)
        self.mark_used(to_evict)
        return to_return

    def write(self, tag, offset, val, do_dirty=True):
        for entry in self.data:
            if entry.tag == tag:
                self.mark_used(entry)
                entry.write(val, offset)
                if do_dirty:
                    entry.dirty = True
                return True
        return False


def clog2(n):
    return int(math.ceil(math.log(n) / math.log(2)))


def binx(i, n):
    r = bin(i)[2:].zfill(n)
    if n == 0:
        return ''
    else:
        return r[-n:]


def hexx(i, n):
    return hex(i)[2:].zfill(int(math.ceil(n / 4.0)))


def int2(s):
    return int(s, 2)


class Cache:

    def __init__(self, line_size, num_sets, num_ways, mem_function):
        self.mem_delta = {}
        self.mem_function = mem_function

        self.line_size = line_size
        self.offset_bits = clog2(line_size)
        self.num_sets = num_sets
        self.index_bits = clog2(self.num_sets)
        self.num_ways = num_ways
        self.tag_bits = addr_size - self.offset_bits - self.index_bits

        self.sets = [Set(num_ways) for i in range(self.num_sets)]

    def parts(self, addr):
        b = binx(addr, addr_size)
        tag = b[0:self.tag_bits]
        idx = b[self.tag_bits:self.tag_bits + self.index_bits]
        off = b[self.tag_bits + self.index_bits:addr_size]
        return tag, idx, off

    def mem_get(self, addr):
        return self.mem_delta.get(addr, self.mem_function(addr))

    def mem_set(self, addr, value):
        self.mem_delta[addr] = value

    def load_line(self, tag, idx):
        cache_line = [0 for i in range(self.line_size)]
        for i in range(self.line_size):
            xaddr = tag + idx + binx(i, self.offset_bits)
            cache_line[i] = self.mem_get(int2(xaddr))

        evicted = self.sets[int2(idx)].insert(tag, cache_line)
        if evicted is not None and evicted.dirty:
            for i in range(len(evicted.data)):
                xaddr = evicted.tag + idx + binx(i, self.offset_bits)
                self.mem_set(int2(xaddr), evicted.data[i])

    def read(self, addr):
        tag, idx, off = self.parts(addr)
        data = self.sets[int2(idx)].get(tag, int2(off))
        hit = True
        if data is None:
            self.load_line(tag, idx)
            hit = False
        data = self.sets[int2(idx)].get(tag, int2(off))
        return hit, data

    def write(self, addr, val):
        tag, idx, off = self.parts(addr)
        if not self.sets[int2(idx)].write(tag, int2(off), val):
            self.load_line(tag, idx)
            self.sets[int2(idx)].write(tag, int2(off), val)
            return False
        else:
            return True

    def init(self, addr, val):
        tag, idx, off = self.parts(addr)
        if not self.sets[int2(idx)].write(tag, int2(off), val):
            self.load_line(tag, idx)
            self.sets[int2(idx)].write(tag, int2(off), val, do_dirty=False)
            return False
        else:
            return True


class BankedCache:

    def __init__(self, num_banks, line_size, num_sets, num_ways, mem_function):
        self.num_banks = num_banks
        self.bank_bits = clog2(self.num_banks)
        self.offset_bits = clog2(line_size)

        def byte_mem_function(addr):
            return mem_function(addr << 2)

        def bmf(bank_id):
            def f(addr):
                b = binx(addr, addr_size - self.bank_bits)
                left = b[0:-self.offset_bits]
                right = b[-self.offset_bits:]
                addrx = int2(left + binx(bank_id, self.bank_bits) + right)
                return byte_mem_function(addrx)
            return f

        self.caches = [Cache(line_size, num_sets, num_ways, bmf(i))
                       for i in range(num_banks)]

    def parts(self, addr):
        b = binx(addr, addr_size)
        left = b[0:-(self.offset_bits + self.bank_bits)]
        bank = b[-self.offset_bits - self.bank_bits:-self.offset_bits]
        right = b[-self.offset_bits:]
        if bank == '':
            bank = '0'
        return int2('0' * self.bank_bits + left + right), int2(bank)

    def read(self, addr):
        addr = addr >> 2  # shift off the lower word offset bits
        addrx, bank = self.parts(addr)
        return self.caches[bank].read(addrx)

    def write(self, addr, val):
        addr = addr >> 2  # shift off the lower word offset bits
        addrx, bank = self.parts(addr)
        return self.caches[bank].write(addrx, val)

    def init(self, addr, val):
        addr = addr >> 2  # shift off the lower word offset bits
        addrx, bank = self.parts(addr)
        return self.caches[bank].init(addrx, val)


def run_trans_seq(cache, trans):
    for thing in trans:
        if type(thing) is list:
            addr, val = thing
            cache.init(addr, val)
            print('I: M[0x%s] <- 0x%s' % (
                  hexx(addr, addr_size), hexx(val, 32)))
        elif type(thing) is tuple:
            addr, val = thing
            hm = 'h' if cache.write(addr, val) else 'm'
            print('W: M[0x%s] <- 0x%s: %s' % (
                  hexx(addr, addr_size), hexx(val, 32), hm))
        else:
            status, data = cache.read(thing)
            hm = 'h' if status else 'm'
            print('R: M[0x%s] -> 0x%s: %s' % (
                  hexx(thing, addr_size), hexx(data, 32), hm))


def main():
    bdc = BankedCache(4, 4, 16, 1, lambda x: 0)
    bac = BankedCache(4, 4, 8, 2, lambda x: 0)
    trans = [
        [0xf00, 0xcafebabe],
        0x0,
        (0x0, 42),
        0xf00,
        0xc0000f00,
        0x0c000f00,
        0xf00,
        (0b00000000000000000000001111001100, 0xdeadbeef),
        (0b10000000000000000000001111001100, 0xc0ffee),
        0b00000000000000000000001111001100,
        0b10000000000000000000001111001100,
        0b11000000000000000000001111001100,
        0b10000000000000000000001111001100,
        0b00000000000000000000001111001100
    ]
    print('Banked Direct Mapped')
    print('#################################')
    run_trans_seq(bdc, trans)

    print('')
    print('')

    print('Banked 2 Way Set Associative')
    print('#################################')
    run_trans_seq(bac, trans)


if __name__ == '__main__':
    main()
