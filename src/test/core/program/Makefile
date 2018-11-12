CC=riscv64-unknown-elf-gcc
# Make sure to build tools with: ./configure --prefix=/opt/riscv --with-arch=rv64im --with-abi=lp64
#CFLAGS= -I. -nostdlib -nostartfiles -static -march=rv64im -mabi=lp64 -O0
CFLAGS= -I. -nostartfiles -static -march=rv64im -mabi=lp64 -O0

SOURCES = $(wildcard *.c)
OBJECTS = $(patsubst %.c,%.out,$(wildcard *.c))
RESET_VECTOR = 0x200

all: $(OBJECTS)

$(OBJECTS): %.out: %.c
	$(CC) -o $@ $< $(CFLAGS) -Wl,--section-start,.start=$(RESET_VECTOR)

all: $(TESTS)

.PHONY: clean
clean:
	rm -f *.o *.out
