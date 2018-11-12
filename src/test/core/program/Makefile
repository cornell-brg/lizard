CC=riscv64-unknown-elf-gcc
CFLAGS= -I. -nostdlib -nostartfiles -static -O1 -march=rv64g
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
