#! /usr/bin/env python2

import random
import sys

def rand_array(minsize, maxsize):
  size = random.randint(minsize, maxsize)
  return [random.randint(-2**31, 2**31 - 1) for i in range(size)]

def main(fun, size=None):
  random.seed(0x00c0ffee)
  for i in range(fun):
    random.randint(0, 10)

  src = rand_array(size or 100, size or 200)
  ref = sorted(src)
  print('int size = %d;' % len(src))
  print('int src[] = {')
  print(', '.join([str(x) for x in src]))
  print('};')
  print('')
  print('int ref[] = {')
  print(', '.join([str(x) for x in ref]))
  print('};')

if __name__ == '__main__':
  main(int(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) == 3 else None)
