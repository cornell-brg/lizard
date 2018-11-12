CC=riscv64-unknown-elf-gcc
CFLAGS= -I. -nostdlib -nostartfiles -static -O1 -march=rv64g
TESTS = basic.out
RESET_VECTOR=0x200

%.out: %.c $(DEPS)
	$(CC) -o $@ $< $(CFLAGS) -Wl,--section-start,.start=$(RESET_VECTOR)

all: $(TESTS)

.PHONY: clean
clean:
	rm -f *.o *.out
