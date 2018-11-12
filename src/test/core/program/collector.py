import glob, os
from subprocess import call

dir_path = os.path.dirname(os.path.realpath(__file__))


def collect():
  os.chdir(dir_path)
  names = [f.rsplit(".", 1)[0] for f in glob.glob("*.c")]
  return (dir_path, names)


def build(fname):
  oname = fname + ".out"
  call(["make", "-C", dir_path, oname])
  return dir_path + '/' + oname
