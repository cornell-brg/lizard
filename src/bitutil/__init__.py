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


def bit_enum(name, *names):
    bits = clog2(len(names))
    data = {}
    short = {}
    for i, spec in enumerate(names):
        if isinstance(spec, tuple):
            key, s_key = spec
        else:
            key, s_key = spec, spec
        data[key] = Bits(bits, i)
        short[i] = s_key
    data['names'] = dict((value, key) for key, value in data.iteritems())
    data['short'] = short
    data['bits'] = bits
    return type(name, (), data)
