#=========================================================================
# ProcFL_alu_test.py
#=========================================================================

import pytest
import random

from pymtl   import *
from harness import *
from lab2_proc.ProcFL import ProcFL

#-------------------------------------------------------------------------
# addi
#-------------------------------------------------------------------------

import inst.rimm.inst_addi as inst_addi

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_addi.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_addi( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# andi
#-------------------------------------------------------------------------

import inst.rimm.inst_andi as inst_andi

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_andi.gen_basic_test     ) ,
  asm_test( inst_andi.gen_dest_dep_test  ) ,
  asm_test( inst_andi.gen_src_dep_test   ) ,
  asm_test( inst_andi.gen_srcs_dest_test ) ,
  asm_test( inst_andi.gen_value_test     ) ,
  asm_test( inst_andi.gen_random_test    ) ,
])
def test_andi( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# ori
#-------------------------------------------------------------------------

import inst.rimm.inst_ori as inst_ori

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_ori.gen_basic_test     ) ,
  asm_test( inst_ori.gen_dest_dep_test  ) ,
  asm_test( inst_ori.gen_src_dep_test   ) ,
  asm_test( inst_ori.gen_srcs_dest_test ) ,
  asm_test( inst_ori.gen_value_test     ) ,
  asm_test( inst_ori.gen_random_test    ) ,
])
def test_ori( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# xori
#-------------------------------------------------------------------------

import inst.rimm.inst_xori as inst_xori

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_xori.gen_basic_test     ) ,
  asm_test( inst_xori.gen_dest_dep_test  ) ,
  asm_test( inst_xori.gen_src_dep_test   ) ,
  asm_test( inst_xori.gen_srcs_dest_test ) ,
  asm_test( inst_xori.gen_value_test     ) ,
  asm_test( inst_xori.gen_random_test    ) ,
])
def test_xori( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# slti
#-------------------------------------------------------------------------

import inst.rimm.inst_slti as inst_slti

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_slti.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_slti( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# sltiu
#-------------------------------------------------------------------------

import inst.rimm.inst_sltiu as inst_sltiu

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_sltiu.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_sltiu( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )
 
#-------------------------------------------------------------------------
# srai
#-------------------------------------------------------------------------

import inst.rimm.inst_srai as inst_srai

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_srai.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_srai( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# srli
#-------------------------------------------------------------------------

import inst.rimm.inst_srli as inst_srli

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_srli.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_srli( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# slli
#-------------------------------------------------------------------------

import inst.rimm.inst_slli as inst_slli

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_slli.gen_basic_test     ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_slli( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# lui
#-------------------------------------------------------------------------

import inst.rimm.inst_lui as inst_lui

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_lui.gen_basic_test    ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_lui( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )

#-------------------------------------------------------------------------
# auipc
#-------------------------------------------------------------------------

import inst.rimm.inst_auipc as inst_auipc

@pytest.mark.parametrize( "name,test", [
  asm_test( inst_auipc.gen_basic_test    ) ,

  # ''' LAB TASK '''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add more rows to the test case table to test more complicated
  # scenarios.
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
])
def test_auipc( name, test, dump_vcd ):
  run_test( ProcFL, test, dump_vcd )
  
