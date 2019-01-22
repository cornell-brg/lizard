import glob, os
from subprocess import call

dir_path = os.path.dirname( os.path.realpath( __file__ ) )


def collect():
  names = [
      os.path.basename( f.rsplit( ".", 1 )[ 0 ] )
      for f in glob.glob( dir_path + "/*.c" )
  ]
  names = [ x for x in names if 'malloc' not in x ]
  return ( dir_path, names )


riscv_tests = """
rv64ui-p-add
rv64ui-p-addi
rv64ui-p-addiw
rv64ui-p-addw
rv64ui-p-and
rv64ui-p-andi
rv64ui-p-auipc
rv64ui-p-beq
rv64ui-p-bge
rv64ui-p-bgeu
rv64ui-p-blt
rv64ui-p-bltu
rv64ui-p-bne
rv64ui-p-fence_i
rv64ui-p-jal
rv64ui-p-jalr
rv64ui-p-lb
rv64ui-p-lbu
rv64ui-p-ld
rv64ui-p-lh
rv64ui-p-lhu
rv64ui-p-lui
rv64ui-p-lw
rv64ui-p-lwu
rv64ui-p-or
rv64ui-p-ori
rv64ui-p-sb
rv64ui-p-sd
rv64ui-p-sh
rv64ui-p-simple
rv64ui-p-sll
rv64ui-p-slli
rv64ui-p-slliw
rv64ui-p-sllw
rv64ui-p-slt
rv64ui-p-slti
rv64ui-p-sltiu
rv64ui-p-sltu
rv64ui-p-sra
rv64ui-p-srai
rv64ui-p-sraiw
rv64ui-p-sraw
rv64ui-p-srl
rv64ui-p-srli
rv64ui-p-srliw
rv64ui-p-srlw
rv64ui-p-sub
rv64ui-p-subw
rv64ui-p-sw
rv64ui-p-xor
rv64ui-p-xori
rv64um-p-div
rv64um-p-divu
rv64um-p-divuw
rv64um-p-divw
rv64um-p-mul
rv64um-p-mulh
rv64um-p-mulhsu
rv64um-p-mulhu
rv64um-p-mulw
rv64um-p-rem
rv64um-p-remu
rv64um-p-remuw
rv64um-p-remw
""".split()


def build_riscv_tests():
  call([ dir_path + "/build-riscv-tests" ] )


def collect_riscv_tests():
  return dir_path + "/riscv-tests/isa/", riscv_tests


def build( fname, opt_level ):
  oname = fname + "-%d.out" % opt_level
  call([ "make", "-C", dir_path, 'OPT_LEVEL=%d' % opt_level, oname ] )
  return dir_path + '/' + oname
