from pymtl import *
import math


def clog2(x):
    return int(math.ceil(math.log(x, 2)))


def bit_enum(name, *names):
    N_BITS = clog2(len(names))
    data = {}
    short = {}
    for i, spec in enumerate(names):
        name, s_name = spec
        data[name] = Bits(N_BITS, i)
        short[data[name]] = s_name
    data['names'] = dict((value, name) for name, value in data.iteritems())
