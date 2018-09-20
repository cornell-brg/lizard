all:
	mkdir -p build && cd build && py.test ../lab2_proc/ -v
tbase:
	mkdir -p build && cd build && py.test ../lab2_proc/ -k test[BASE -v
talt:
	mkdir -p build && cd build && py.test ../lab2_proc/ -k test[ALT -v
tfl:
	mkdir -p build && cd build && py.test ../lab2_proc/ -k test[FL -v

call:
	mkdir -p build && cd build && py.test ../lab3_mem/test/auto_cache_test.py -v
cbase:
	mkdir -p build && cd build && py.test ../lab3_mem/test/auto_cache_test.py -v -k test[BASE
calt:
	mkdir -p build && cd build && py.test ../lab3_mem/test/auto_cache_test.py -v -k test[ALT
cfl:
	mkdir -p build && cd build && py.test ../lab3_mem/test/auto_cache_test.py -v -k test[FL

nall:
	mkdir -p build && cd build && py.test ../lab4_net/test -v
nbench:
	mkdir -p build && cd build && ../lab4_net/benchmark.sh | tee ../../reports/lab4_net/raw_benchmarks.txt

mall:
	mkdir -p build && cd build && py.test ../lab5_mcore/test -v
