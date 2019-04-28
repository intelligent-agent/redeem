import os
import platform
kernel_version = platform.release().split('.')
boards = [["Darwin", "{}_{}".format(kernel_version[0], kernel_version[1])],
          ["FakePrinter", None]]
from . import Darwin, FakePrinter


def local_cf(x):
  the_file = os.path.normpath(
      os.path.join(
          os.path.dirname(__file__), '..', '..', '..', '..', '..', '..', '..', 'etc', '{}.conf'.format(x)
      )
  )
  return the_file
