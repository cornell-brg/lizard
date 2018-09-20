from lab3_mem.test.auto_cache_test import r, w, i


def read_miss_eviction_test(base_addr):
    return [
        w(0x00000000, 0xcafebabe),
        r(0x0000a000),
    ], {
        0x0000a000: 0xdeadbeef,
    }


def write_miss_eviction_test(base_addr):
    return [
        w(0x00000000, 0xcafebabe),
        w(0x0000a000, 0xbabebabe),
        r(0x0000a000)
    ], {
        0x0000a000: 0xdeadbeef,
    }


def capacity_test(base_addr):
    return [
        w(a << 4, a << 4) for a in range(0, 16)
    ] + [
        w(0x00000ff0, 0xcafebabe),
    ] + [
        r(a << 4) for a in range(0, 16)
    ] + [
        r(0x00000ff0)
    ]


def read_hit_test(base_addr):
    return [
        w(0x00000000, 0xdeadbeef),
        w(0x00000080, 0x00c0ffee),
        r(0x00000000),
        r(0x00000080)
    ]


def read_miss_write_hit_test(base_addr):
  return [
    r(0x0000006c),
    w(0x00000060, 0xdeadbeef)
  ]


def read_miss_write_hit2_test(base_addr):
  return [
    r(0x0000006c),
    w(0x00000070, 0x00c0ffee),
    w(0x00000060, 0xdeadbeef)
  ]
