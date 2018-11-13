OPT_LEVEL=0
CC=riscv64-unknown-elf-gcc
# Make sure to build tools with: ./configure --prefix=/opt/riscv --with-arch=rv64im --with-abi=lp64
#CFLAGS= -I. -nostdlib -nostartfiles -static -march=rv64im -mabi=lp64 -O0
CFLAGS= -I. -static -march=rv64im -mabi=lp64 -O$(OPT_LEVEL)

OBJECTS = $(patsubst %.c,%-$(OPT_LEVEL).out,$(wildcard *.c))
RESET_VECTOR = 0x200
EXCEPTION_VECTOR = 0x0

all: $(OBJECTS)

$(OBJECTS): %-$(OPT_LEVEL).out: %.c
	$(CC) -o $@ $< $(CFLAGS) -Wl,--section-start,.start=$(RESET_VECTOR),--section-start,.exception_handler=$(EXCEPTION_VECTOR)

all: $(TESTS)

.PHONY: clean
clean:
	rm -f *.o *.out
