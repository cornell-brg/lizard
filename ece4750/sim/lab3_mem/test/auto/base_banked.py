from lab3_mem.test.auto_cache_test import r, w, i


def no_conflict(base_addr):
    '''
    1 bank:
    0x00000300
        tag     0x00000003
        index   0x00000000
        offset  0x00000000
    0x00000000
        tag     0x00000000
        index   0x00000000
        offset  0x00000000

    4 banks:
    0x00000300
        tag     0x00000000
        index   0x0000000c
        bank    0x00000000
        offset  0x00000000
    0x00000000
        tag     0x00000000
        index   0x00000000
        bank    0x00000000
        offset  0x00000000

    Would be a conflict with a direct mapped 1 bank, but
    should not be a conflict with a 4 banked design.
    '''
    return [
        w(0x00000300, 0xcafebabe), # index 0x1, bank 0x2
        w(0x00000000, 0xdeadbeef), # index 0x1, bank 0x3
        r(0x00000300), # index 0x1, bank 0x2 - should hit
        r(0x00000000), # index 0x1, bank 0x3 - should hit
    ]
