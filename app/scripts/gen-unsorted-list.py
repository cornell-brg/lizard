#!/usr/bin/env python
#===============================================================================
# gen-unsorted-list.py
#===============================================================================
# Generate random numbers for merge sort benchmark.
#
#  -h --help     Display this message
#  -v --verbose  Verbose mode
#
# Author : Ji Kim
# Date   : October 12, 2011

import optparse
import fileinput
import sys
import re
import math
import random

#-------------------------------------------------------------------------------
# Command line processing
#-------------------------------------------------------------------------------

class OptionParserWithCustomError(optparse.OptionParser):
  def error( self, msg = "" ):
    if ( msg ): print("\n ERROR: %s" % msg)
    print("")
    for line in fileinput.input(sys.argv[0]):
      if ( not re.match( "#", line ) ): sys.exit(msg != "")
      if ((fileinput.lineno() == 3) or (fileinput.lineno() > 4)):
        print( re.sub( "^#", "", line.rstrip("\n") ) )

def parse_cmdline():
  p = OptionParserWithCustomError( add_help_option=False )
  p.add_option( "-v", "--verbose", action="store_true", dest="verbose" )
  p.add_option( "-h", "--help",    action="store_true", dest="help" )
  p.add_option( "-n", "--size",    action="store", type="int", dest="size" )
  (opts,args) = p.parse_args()
  if ( help == True ): p.error()
  if args: p.error("found extra positional arguments")
  return opts

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

def main():
  opts = parse_cmdline()

  # Open vmh file for writing
  test_out = open( "ubmark-merge-sort.dat", "w" )

  test_out.write( "// Data set for ubmark-merge-sort\n\n" );

  list = []

  try:

    # Write source array
    test_out.write( "int src[] = {\n" );

    for i in range( opts.size ):
      #roll = random.randint( -pow( 2, 31 ) + 1, pow( 2, 31 ) - 1 )
      roll = random.randint( -pow( 2, 16 ), pow( 2, 16 ) )
      list.append( roll )
      test_out.write( "  " + str( roll ) + ",\n" )

    test_out.write( "};\n\n" );

    # Sort list
    list.sort()

    # Write reference array
    test_out.write( "int ref[] = {\n" );

    for i in range( len( list ) ):
      test_out.write( "  " + str( list[i] ) + ",\n" )

    test_out.write( "};\n\n" );

  finally:

    test_out.close()

main()

