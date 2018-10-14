from pymtl import *


def clog2(x):
    # Could be implemented with int(math.ceil(math.log(x, 2))),
    # but might cause strange floating point issues
    i = 0
    v = 1
    while x > v:
        v *= 2
        i += 1
    return i


def sane_lookup(d):
    @staticmethod
    def f(k):
        if isinstance(k, Bits):
            k = int(k)
        return d[k]

    return f


def bit_enum(name, bits=None, *names, **pairs):
    assert not (names and pairs)
    if pairs:
        assert bits
    else:
        min_bits = clog2(len(names))
        bits = bits or clog2(len(names))
        assert bits >= min_bits

    data = {}
    short = {}
    for i, spec in enumerate(names):
        if isinstance(spec, tuple):
            key, s_key = spec
        else:
            key, s_key = spec, spec
        data[key] = Bits(bits, i)
        short[i] = s_key
    for key, value in pairs.iteritems():
        data[key] = Bits(bits, value)
        short[int(value)] = key

    names_dict = dict((int(value), key) for key, value in data.iteritems())
    data['name'] = sane_lookup(names_dict)
    data['short'] = sane_lookup(short)
    data['bits'] = bits
    return type(name, (), data)
