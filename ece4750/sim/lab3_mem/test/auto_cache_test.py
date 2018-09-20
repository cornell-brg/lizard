import pytest
from pclib.test import run_sim
from cache_sim import BankedCache

from BlockingCacheFL_test import TestHarness
from BlockingCacheFL_test import req, resp

from lab3_mem.BlockingCacheFL import BlockingCacheFL
from lab3_mem.BlockingCacheBaseRTL import BlockingCacheBaseRTL
from lab3_mem.BlockingCacheAltRTL import BlockingCacheAltRTL

from lab3_mem.test import auto
import pkgutil
import importlib
import inspect
import random

random.seed(0xa4e28cc2)

max_cycles = 20000
enforce_hits = True

line_count = 16
max_opaque = 256

cache_dict = {
    'ALT': BlockingCacheAltRTL,
    'BASE': BlockingCacheBaseRTL,
    'FL': BlockingCacheFL
}

cache_way_dict = {
    'ALT': 2,
    'BASE': 1,
    'FL': 1
}

cache_check_dict = {
    'ALT': True,
    'BASE': True,
    'FL': False
}

cache_stall_dict = {'nd': 0.0, 'rd': 0.5}
cache_lat_dict = {'nd': 0, 'rd': 3}
cache_src_dict = {'nd': 0, 'rd': 3}
cache_sink_dict = {'nd': 0, 'rd': 5}


def w(addr, data):
    return ('W', addr, data)


def r(addr):
    return ('R', addr)


def i(addr, data):
    return ('I', addr, data)

def extract_bank(addr):
  addrb = bin(addr)[2:].zfill(32)
  return int(addrb[26:28], 2)


def split_by_bank(seq):
    split = [[] for i in range(4)]
    for trans in seq:
        split[extract_bank(trans[1])].append(trans)
    return split


def gen_msg_seq(seq, num_banks, num_ways, memory_map={}):
    def memory_function(addr):
        return memory_map.get(addr, 0)

    cache = BankedCache(num_banks, 4, line_count /
                        num_ways, num_ways, memory_function)
    opaque = 0
    reqs = []
    resps = []
    for r in seq:
        if r[0] == 'W':
            hit = cache.write(r[1], r[2])
            test = 1 if hit else 0
            request = req('wr', opaque, r[1], 0, r[2])
            response = resp('wr', opaque, test, 0, 0)
        elif r[0] == 'R':
            hit, data = cache.read(r[1])
            test = 1 if hit else 0
            request = req('rd', opaque, r[1], 0, 0)
            response = resp('rd', opaque, test, 0, data)
        elif r[0] == 'I':
            hit = cache.init(r[1], r[2])
            test = 1 if hit else 0
            request = req('in', opaque, r[1], 0, r[2])
            response = resp('in', opaque, 0, 0, 0)

        reqs += [request]
        resps += [response]
        opaque = (opaque + 1) % 256

    return (reqs, resps)


def auto_modules():
    modules = []
    for _, cat, _ in pkgutil.iter_modules(path=auto.__path__):
        modules += [importlib.import_module(auto.__name__ + '.' + cat)]
    return modules


def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod


def list_functions(mod):
    return [func for
            func in mod.__dict__.itervalues() if is_mod_function(mod, func)]


def clean_module_name(m, n=1):
    return '-'.join(m.__name__.split('.')[-n:])


def get_test_pair(func):
    name = func.__name__
    if name.endswith("_test"):
        name = name[:-5]
    return (name, func)


def extract_module_tests(m):
    funcs = [f for f in list_functions(m) if f.__name__.endswith('_test')]
    result = [('{}-{}'.format(clean_module_name(m), name), func)
              for name, func in [get_test_pair(f) for f in funcs]]
    return result


def extract_tests(ms):
    return [test_pair for m in ms for test_pair in extract_module_tests(m)]


def idfn(val):
    return val[0]


@pytest.mark.parametrize('rand_delays', ['rd', 'nd'])
@pytest.mark.parametrize('num_banks', [1, 4], ids=lambda x: '%d_bank' % x)
@pytest.mark.parametrize('name_and_test',
                         extract_tests(auto_modules()), ids=idfn)
@pytest.mark.parametrize('cache_key', cache_dict.keys())
def test(num_banks, cache_key, name_and_test, rand_delays, dump_vcd):
    test = name_and_test[1]
    impl = cache_dict[cache_key]
    check_hits = cache_check_dict[cache_key] and enforce_hits
    num_ways = cache_way_dict[cache_key]

    # Zero for the base address
    test_gen = test(0)
    if type(test_gen) is tuple:
        input_msgs, input_mem = test_gen
    else:
        input_msgs, input_mem = test_gen, {}

    stall = cache_stall_dict[rand_delays]
    lat = cache_lat_dict[rand_delays]
    src = cache_src_dict[rand_delays]
    sink = cache_sink_dict[rand_delays]

    if num_banks == 1:
        input_msg_vector = [input_msgs]
    else:
        input_msg_vector = split_by_bank(input_msgs)

    for msg_seq in input_msg_vector:
        reqs, resps = gen_msg_seq(msg_seq, num_banks, num_ways, input_mem)

        # Instantiate testharness
        harness = TestHarness(reqs, resps, stall, lat, src, sink,
                              impl, num_banks,
                              check_hits, dump_vcd)

        # Load memory before the test
        harness.load(input_mem.keys(), input_mem.values())
        # Run the test
        run_sim(harness, dump_vcd, max_cycles=max_cycles)
