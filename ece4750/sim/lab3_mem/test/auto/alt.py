from lab3_mem.test.auto_cache_test import r, w, i


def read_miss_eviction_test(base_addr):
    return [
        w(0x00000000, 0xcafebabe),
        w(0x00000100, 0xd00df00d),
        r(0x00000200),
        r(0x00000000),
        r(0x00000100)
    ]


def write_miss_eviction_test(base_addr):
    return [
        w(0x00000000, 0xcafebabe),
        w(0x00000100, 0xd00df00d),
        w(0x00000200, 0xf00df00d),
        w(0x00000000, 0xa000b000),
        w(0x00000100, 0xabcddcba),
        r(0x00000000),
        r(0x00000100),
        r(0x00000200)
    ]


def capacity_test(base_addr):
    return [
        w(a << 4, a << 4) for a in range(0, 8)
    ] + [
        w((a << 4) + 0xf00, (a << 4) + 0xf00) for a in range(0, 8)
    ] + [
        w(0x00000ff0, 0xcafebabe),
    ] + [
        r(a << 4) for a in range(0, 8)
    ] + [
        r((a << 4) + 0xf00) for a in range(0, 8)
    ] + [
        r(0x00000ff0)
    ]


def read_hit_test(base_addr):
    return [
        w(0x00000000, 0xdeadbeef),
        w(0x00001000, 0x00c0ffee),
        r(0x00000000),
        r(0x00001000)
    ]


def read_lru_test(base_addr):
    return [
        r(0x00000000),
        r(0x00010000),
        r(0x00020000),
        r(0x00030000),
    ], {
        0x00000000: 0xdeadbeef,
        0x00010000: 0x00c0ffee,
        0x00020000: 0xb00bb00b,
        0x00030000: 0x12345678,
    }


def write_lru_single_test(base_addr):
    return [
        w(0x000000f0, 0xdeadbeef),
        w(0x000001f0, 0x00c0ffee),
        w(0x000002f0, 0xcafebabe),
        r(0x000001f0)
    ]


def write_lru_big_double_test(base_addr):
    return [
        w(0x000000f0, 0xdeadbeef),
        w(0x000001f0, 0x00c0ffee),
        w(0x000002f0, 0xcafebabe),
        w(0x000003f0, 0x66666666),
        r(0x000000f0),
        r(0x000001f0),
        r(0x000002f0),
        r(0x000003f0),
    ]
