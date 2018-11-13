import glob, os
from subprocess import call

dir_path = os.path.dirname( os.path.realpath( __file__ ) )


def collect():
  os.chdir( dir_path )
  names = [ f.rsplit( ".", 1 )[ 0 ] for f in glob.glob( "*.c" ) ]
  return ( dir_path, names )


def collect_bin():
  os.chdir( dir_path + "/bin" )
  names = glob.glob( "rv64ui*" )
  return ( dir_path + "/bin/", names )


def build( fname, opt_level ):
  oname = fname + "-%d.out" % opt_level
  call([ "make", "-C", dir_path, 'OPT_LEVEL=%d' % opt_level, oname ] )
  return dir_path + '/' + oname
