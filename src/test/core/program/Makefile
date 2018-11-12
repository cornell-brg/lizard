CC=riscv64-unknown-elf-gcc
CFLAGS= -I. -nostdlib -nostartfiles -O0 -march=rv64g
TESTS = basic.out
RESET_VECTOR=0x200

%.out: %.c $(DEPS)
	$(CC) -o $@ $< $(CFLAGS) -Wl,--section-start,.text=$(RESET_VECTOR)

all: $(TESTS)

.PHONY: clean
clean:
	rm -f *.o *.out
