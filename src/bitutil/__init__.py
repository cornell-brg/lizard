from pymtl import *
import math


def clog2(x):
    return int(math.ceil(math.log(x, 2)))


def bit_enum(name, *names):
    bits = clog2(len(names))
    data = {}
    short = {}
    for i, spec in enumerate(names):
        key, s_key = spec
        data[key] = Bits(bits, i)
        short[i] = s_key
    data['names'] = dict((value, key) for key, value in data.iteritems())
    data['short'] = short
    data['bits'] = bits
    return type(name, (), data)
