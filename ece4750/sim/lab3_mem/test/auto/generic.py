from lab3_mem.test.auto_cache_test import r, w, i


def read_hit_clean_test(base_addr):
    return [
        i(base_addr, 0xdeadbeef),
        r(base_addr)
    ]

def write_hit_clean_test(base_addr):
    return [
        i(base_addr, 0x0a0b0c0d),
        w(base_addr, 0xbeefbeeb),
        r(base_addr)
    ]

def read_hit_dirty_test(base_addr):
    return [
        i(base_addr, 0xdeadbeef),
        w(base_addr, 0xcafebabe),
        r(base_addr)
    ]

def write_hit_dirty_test(base_addr):
    return [
        i(base_addr, 0xdeadbeef),
        w(base_addr, 0xcafebabe),
        w(base_addr, 0xdeadbabe),
        r(base_addr)
    ]

def read_miss_refill_test(base_addr):
    return [
        r(0x00000000),
        r(0x00000004)
    ], {
        0x00000000: 0xdeadbeef,
        0x00000004: 0x00c0ffee,
    }

def wite_miss_refill_test(base_addr):
    return [
        w(0x00000000, 0xdeadbeef),
        w(0x00000004, 0x00c0ffee),
        r(0x00000000),
        r(0x00000004)
    ], {
        0x00000000: 0xdeadbeef,
        0x00000004: 0x00c0ffee,
    }

def read_miss_eviction_test(base_addr):
    return [
        r(0x00000000),
        r(0x00000004)
    ], {
        0x00000000: 0xdeadbeef,
        0x00000004: 0x00c0ffee,
    }

def wite_miss_refill_test(base_addr):
    return [
        w(0x00000000, 0x66666666),
        w(0x00000004, 0x55555555),
        r(0x00000000),
        r(0x00000004)
    ], {
        0x00000000: 0xdeadbeef,
        0x00000004: 0x00c0ffee,
    }
