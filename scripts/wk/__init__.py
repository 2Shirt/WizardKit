'''WizardKit: wk module init'''
# vim: sts=2 sw=2 ts=2

import sys

from wk import cfg
from wk import exe
from wk import hw
from wk import io
from wk import kit
from wk import log
from wk import net
from wk import os
from wk import std
from wk import sw


# Check env
if sys.version_info < (3, 5):
  # Unsupported
  raise RuntimeError(
    'This package is unsupported on Python {major}.{minor}'.format(
      **sys.version_info,
      ))
if sys.version_info < (3, 7):
  # Untested
  raise UserWarning(
    'Python {major}.{minor} is untested for this package'.format(
      **sys.version_info,
      ))

# Init
log.start()


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
