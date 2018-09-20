from lab3_mem.test.auto_cache_test import r, w, i
import random

address_cap = 2**32
address_mask = 0xFFFFFFFC
value_cap = 2**32


def gen_random_seq(base, span, n, mask=0xFFFFFFFF):
    seq = [None] * n
    for x in range(n):
        addr = (random.randint(0, span) + base) % address_cap
        addr &= address_mask
        addr &= mask
        if random.choice([True, False]):
            data = random.randint(0, address_cap - 1)
            seq[x] = w(addr, data)
        else:
            seq[x] = r(addr)
    return seq


def single_line_local_test(base_addr):
    return gen_random_seq(base_addr, 0xFFFFF, 1000, 0xFFFFFF00)

def double_line_local_test(base_addr):
    return gen_random_seq(base_addr, 0xFFFFF, 1000, 0xFFFFFE00)

def small_local_test(base_addr):
    return gen_random_seq(base_addr, 0x199, 1000)

def small_wide_test(base_addr):
    return gen_random_seq(0, 0xFFFFF, 1000)

def small_narrow_test(base_addr):
    return gen_random_seq(base_addr, 0xFF, 1000)
