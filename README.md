[![Build Status](https://travis-ci.com/cornell-brg/lizard.svg?token=ZakjYd6szqJoghAvvsaY&branch=master)](https://travis-ci.com/cornell-brg/lizard)
# The Lizard Core :lizard:

The Lizard Core was designed by Jacob Glueck and Aaron Wisner during the Fall 2018
and Spring 2019 semesters as a Master's of Engineering project at Cornell University.
The Lizard Core is synthesizable, out-of-order, RISC-V RV64IM core written in PyMTL.
It can meet timing at 350 MHz in a 45 nm standard cell-based design flow.

![alt text](https://github.com/cornell-brg/lizard/images/lizard-pipeline-diagram.png "Lizard Pipeline")

Detailed information about the design of the core is [available in the report](https://github.com/cornell-brg/lizard/releases/download/v1.0.0/lizard-core-report.pdf).

## Installation

### Perquisites

Lizard requires:

-   Python 2.

-   PyMTL: <https://github.com/cornell-brg/pymtl>.

-   Verilator: <https://www.veripool.org/wiki/verilator>. Note that is
    possible to simulate the processor, albeit slowly, without
    Verilator. To generate Verilog or simulate it faster, Verilator is
    required.

-   A GCC RISCV toolchain:
    <https://github.com/riscv/riscv-gnu-toolchain>. The toolchain is
    required for running tests and compiling interesting programs to
    run. To target Lizard, the toolchain must be configured with
    `–with-arch=rv64im –with-abi=lp64`. In theory, a multilib compiler
    should also work (complied with `–enable-multilib`), however the
    default set of architectures and ABIs generated for a multilib
    compiler does not include `rv64im-lp64`. It is possible to patch the
    compiler sources to achieve this, however. See:
    <https://github.com/orangeturtle739/panther/blob/master/sys-devel/riscv-gnu-toolchain/files/multilib-rv64im-lp64.patch>.

### Installing

The Lizard core can be found on Github:
<https://github.com/cornell-brg/lizard>. The preferred way to install
and experiment with it is via `pip` (the Package Installer for Python),
as `pip` will handle all dependencies automatically.

To install via `pip`:
```
git clone https://github.com/cornell-brg/lizard
pip2 install --user -e lizard
```

The above installation will allow simulation and Verilog generation, but
the tests might not work. To install the test dependencies as well, use:
```
pip2 install --user -e lizard[test]
```

Installing via `pip` will also install two executables, `lizard-sim` and
`lizard-gen`, either into `~/.local/bin` or into the `bin` directory of
a virtual environment, if using a virtual environment.

Note that is is possible to install without `pip`, but not recommended
as the proper dependencies may not be installed. However, to use lizard
without `pip`, simply clone the repository:
```
git clone https://github.com/cornell-brg/lizard
```
The two scripts will be `lizard/sim.py` and `lizard/gen_verilog.py`,
and can be manually invoked.

### Running tests

Lizard uses pytest with the coverage plugin for testing. Running the
tests requires that verilator and `riscv64-unknown-elf-gcc` be on the
`PATH`. The tests can be run from the root of the repository:
```
mkdir build
cd build
pytest ../tests
```
While running, the tests generate waveforms in `.vcd` files, as well as
Verilog and other artifacts, and running the tests in a temporary
`build` directory contains these artifacts. Note that the tests take
about 5 hours to run, and unfortunately cannot be run in parallel with
`pytest-xdist` due to race conditions when compiling code and generating
Verilog.

## Simulating Lizard

### Writing C Programs

The Lizard core can run most simple C programs, as long as they do not
attempt to make any system calls. The programs have to be statically
linked, and must have the first instruction at `0x200`, the core’s reset
vector. In order to make this easy to do, Lizard comes with a C build
system and minimal runtime library in the `app` directory. The build
system contains a linker script, and handles the GCC `-march` and
`-mabi` flags, as well as some others. The runtime library is very
simple, and contained in the `app/common` folder. It contains:

-   A `crt0.s` assembly program which contains the `_start` symbol.
    This program configures the stack pointer and the global pointer,
    and then dispatches the `_runtime_start` function.

-   `runtime_start.c`, which defines the `_runtime_start` function.
    This function configures a simple exception handler, which prints
    information about the exception and then aborts the program. Then,
    it invokes `main()`, with no arguments. After the conclusion of
    `main()`, it sends a special signal through the processor debug bus
    with the return code, which causes the simulator to exit with the
    same return code.

-   `csr_utils.h` contains various macros and functions for reading and
    writing the Control Status Registers (CSRs), including reading and
    writing from the processor debug bus.

-   `common_print.h` defines a series of functions for printing
    information through the simulator. These functions work by sending
    data to the simulator through the processor debug bus. The simulator
    then prints the data. The main function defined here is
    `lizard_printf(const char\* format, ...)`, which functions almost
    like `printf`. However, it has a maximum length of 65536 characters,
    and some format strings might not work. Internally, it uses
    `snprintf`, which for some format strings, attempts to call
    `malloc`. There are ways to fix this, but this runtime was designed
    to be minimal. Luckily, it appears that only floating point
    specifiers cause this problem.

-   `common_misc.h` contains a series of benchmarking tools tools,
    which manipulate the `minstret` and `mcycle` CSRs.

-   `common.h` includes `common_misc.h`, `common.h`, and (indirectly),
    `csr_utils.h`. User programs should simply include `common.h` to
    have access the runtime.

The easiest way to write a new program is to add make a C file in the
`ubmark` directory, and add the file to `ubmark.mk.in`. For more complex
programs, another subproject might be required. `ubmark/hello-world.c`,
shown below, is a simple example program:
```c
    #include "common.h"
    #include "string.h"

    int main() {
      const char* s1 = "alpha";
      const char* s2 = "beta";

      if (strcmp(s1, s2) < 0) {
        lizard_print("s1 was first\n");
      } else {
        lizard_print("s2 was first\n");
      }

      lizard_print("Hello World!\n");
      lizard_printf("The best number is: %d\n", 42);

      return 42;
    }
```

### Compiling

To compile a program, run `./setup` in the `app` directory. Then, run
`make` in the newly-created `build` directory.

### Simulating with ELF files

Simulating an ELF file is simple with the `lizard-sim` tool. The usage
is:
```
$ lizard-sim -h
usage: lizard-sim [-h] [--trace] [--vcd] [--verilate] [--use-cached]
                  [--maxcycles MAXCYCLES] [--imem-delay IMEM_DELAY]
                  [--dmem-delay DMEM_DELAY]
                  elf_file

Simulate the Lizard Core running an ELF file

positional arguments:
  elf_file              the ELF file to run

optional arguments:
  -h, --help            show this help message and exit
  --trace               set to print out a line trace while the program runs
  --vcd                 set to generate a waveform .vcd file
  --verilate            set to simulate with a verilated model
  --use-cached          use a cached verilated model
  --maxcycles MAXCYCLES
                        maximum number of cycles to simulate
  --imem-delay IMEM_DELAY
                        imem delay
  --dmem-delay DMEM_DELAY
                        dmem delay
```

To run it on the hello world program, using the Python simulation:
```
$ time lizard-sim ../app/build/hello-world
s1 was first
Hello World!
The best number is: 42

real    1m3.993s
user    1m3.857s
sys     0m0.118s
$ echo $?
42
```

Note that the exit status is preserved! The verilated version is much
faster:
```
$ time lizard-sim ../app/build/hello-world --verilate
s1 was first
Hello World!
The best number is: 42

real    0m19.089s
user    0m18.704s
sys     0m0.372s
$ echo $?
42
```

## Generating Verilog

To generate Verilog, run `lizard-gen`. The Verilog, and a couple other
files, will be created in the working directory. The Verilog is
`proc.sv`.

### Using the ASIC Toolflow

The ASIC toolflow is contained inside the `asic` directory. It is based
off of the Alloy Asic project
(<https://github.com/cornell-brg/alloy-asic>). Provided all the required
tools are installed and environment variables configured, the processor
can be pushed through the flow with:
```
cd asic
mkdir build
cd proc
make
cd ../build
../configure design=megaproc
make
```

Using the ASIC flow is difficult because it requires a number of
programs and other libraries, and this procedue likely won’t work unless
you are a student in the Batten Research Group using one of our servers.
