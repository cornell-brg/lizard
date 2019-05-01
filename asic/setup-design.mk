#=========================================================================
# setup-design.mk
#=========================================================================
# Here we select the design to push as well as its top-level Verilog
# module name, the clock target, and the Verilog source file.
#
# Author : Christopher Torng
# Date   : March 26, 2018

#-------------------------------------------------------------------------
# Tutorial 6 Designs
#-------------------------------------------------------------------------

# Sort Unit

ifeq ($(design),megaproc)
  design_name   = proc
  synth_period  = 2.9
  clock_period  = 3.0
  design_v      = ../proc/proc.sv
  activity_vcd  = ../proc/ubmark-vvadd-verilate.verilator.vcd
endif

ifeq ($(design),sort-unit)
  design_name   = SortUnitStructRTL_8nbits
  clock_period  = 1.0
  design_v      = ../../sim/build/SortUnitStructRTL_8nbits.v
  activity_vcd  = ../../sim/build/sort-rtl-struct-random.verilator1.vcd
endif

# GCD Unit

ifeq ($(design),gcd-unit)
  design_name   = GcdUnitRTL
  clock_period  = 1.0
  design_v      = ../../sim/build/GcdUnitRTL.v
  activity_vcd  = ../../sim/build/gcd-rtl-random.verilator1.vcd
endif

#-------------------------------------------------------------------------
# Tutorial 8 Designs
#-------------------------------------------------------------------------

# Example of using SRAMs from PyMTL (ValRdy wrapper of SRAM)

ifeq ($(design),tut8-sram)
  design_name   = SramValRdyRTL
  clock_period  = 1.0
  design_v      = ../../sim/build/SramValRdyRTL_blackbox.v
  activity_vcd  = ../../sim/build/sram-rtl-random.verilator1.vcd
  srams_dir     = ../../sim/sram
  srams         = SRAM_64x64_1P
endif

#-------------------------------------------------------------------------
# Tutorial 9 Designs
#-------------------------------------------------------------------------

# vvadd accelerator in isolation

ifeq ($(design),tut9-vvadd-xcel)
  design_name   = VvaddXcelRTL
  clock_period  = 1.5
  design_v      = ../../sim/build/VvaddXcelRTL.v
  activity_vcd  = ../../sim/build/vvadd-xcel-rtl-multiple.verilator1.vcd
endif

# processor plus null accelerator

ifeq ($(design),tut9-pmx-null)
  design_name   = ProcMemXcel_null_rtl
  clock_period  = 1.5
  design_v      = ../../sim/build/ProcMemXcel_null_rtl_blackbox.v
  activity_vcd  = ../../sim/build/pmx-sim-null-rtl-ubmark-vvadd.verilator1.vcd
  srams_dir     = ../../sim/sram
  srams         = SRAM_128x256_1P SRAM_32x256_1P
endif

# processor plus vvadd accelerator

ifeq ($(design),tut9-pmx-vvadd)
  design_name   = ProcMemXcel_vvadd_rtl
  clock_period  = 1.5
  design_v      = ../../sim/build/ProcMemXcel_vvadd_rtl_blackbox.v
  activity_vcd  = ../../sim/build/pmx-sim-vvadd-rtl-ubmark-vvadd-xcel.verilator1.vcd
  srams_dir     = ../../sim/sram
  srams         = SRAM_128x256_1P SRAM_32x256_1P
endif

#-------------------------------------------------------------------------
# Lab 1 Designs
#-------------------------------------------------------------------------

# Fixed Latency Multiplier

ifeq ($(design),lab1-imul-fixed)
  design_name   = IntMulFixedLatRTL
  clock_period  = 0.5
  design_v      = ../../sim/build/IntMulFixedLatRTL.v
  activity_vcd  = ../../sim/build/imul-rtl-fixed-small.verilator1.vcd
endif

# Variable Latency Multiplier

ifeq ($(design),lab1-imul-var)
  design_name   = IntMulVarLatRTL
  clock_period  = 0.5
  design_v      = ../../sim/build/IntMulVarLatRTL.v
  activity_vcd  = ../../sim/build/imul-rtl-var-small.verilator1.vcd
endif

# Single-Cycle Multiplier

ifeq ($(design),lab1-imul-scycle)
  design_name   = IntMulScycleRTL
  clock_period  = 1.0
  design_v      = ../../sim/build/IntMulScycleRTL.v
  activity_vcd  = ../../sim/build/imul-rtl-scycle-small.verilator1.vcd
endif

# 1-stage Pipelined Multiplier

ifeq ($(design),lab1-imul-1stage)
  design_name   = IntMulNstageRTL_1stage
  clock_period  = 10.0
  design_v      = ../../sim/build/IntMulNstageRTL_1stage.v
  activity_vcd  = ../../sim/build/imul-rtl-1stage-small.verilator1.vcd
endif

# 2-stage Pipelined Multiplier

ifeq ($(design),lab1-imul-2stage)
  design_name   = IntMulNstageRTL_2stage
  clock_period  = 10.0
  design_v      = ../../sim/build/IntMulNstageRTL_2stage.v
  activity_vcd  = ../../sim/build/imul-rtl-2astage-small.verilator1.vcd
endif

# 4-stage Pipelined Multiplier

ifeq ($(design),lab1-imul-4stage)
  design_name   = IntMulNstageRTL_4stage
  clock_period  = 10.0
  design_v      = ../../sim/build/IntMulNstageRTL_4stage.v
  activity_vcd  = ../../sim/build/imul-rtl-4astage-small.verilator1.vcd
endif

# 8-stage Pipelined Multiplier

ifeq ($(design),lab1-imul-8stage)
  design_name   = IntMulNstageRTL_8stage
  clock_period  = 10.0
  design_v      = ../../sim/build/IntMulNstageRTL_8stage.v
  activity_vcd  = ../../sim/build/imul-rtl-8astage-small.verilator1.vcd
endif

#-------------------------------------------------------------------------
# Lab 2 Designs
#-------------------------------------------------------------------------

# sort accelerator in isolation

ifeq ($(design),lab2-sort-xcel)
  design_name   = SortXcelRTL
  clock_period  = 1.5
  design_v      = ../../sim/build/SortXcelRTL.v
  activity_vcd  = ../../sim/build/sort-xcel-rtl-random.verilator1.vcd
endif

# processor plus null accelerator

ifeq ($(design),lab2-pmx-null)
  design_name   = ProcMemXcel_null_rtl
  clock_period  = 1.5
  design_v      = ../../sim/build/ProcMemXcel_null_rtl_blackbox.v
  activity_vcd  = ../../sim/build/pmx-sim-null-rtl-ubmark-sort.verilator1.vcd
  srams_dir     = ../../sim/sram
  srams         = SRAM_128x256_1P SRAM_32x256_1P
endif

# processor plus sort accelerator

ifeq ($(design),lab2-pmx-sort)
  design_name   = ProcMemXcel_sort_rtl
  clock_period  = 1.5
  design_v      = ../../sim/build/ProcMemXcel_sort_rtl_blackbox.v
  activity_vcd  = ../../sim/build/pmx-sim-sort-rtl-ubmark-sort-xcel.verilator1.vcd
  srams_dir     = ../../sim/sram
  srams         = SRAM_128x256_1P SRAM_32x256_1P
endif

#-------------------------------------------------------------------------
# Export
#-------------------------------------------------------------------------

export design_name
