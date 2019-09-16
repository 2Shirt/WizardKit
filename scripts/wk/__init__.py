"""WizardKit: wk module init"""
# vim: sts=2 sw=2 ts=2

from sys import version_info as version

from wk import cfg
from wk import hw
from wk import io
from wk import kit
from wk import log
from wk import net
from wk import os
from wk import std
from wk import sw


# Check env
if version < (3, 7):
  # Unsupported
  raise RuntimeError(
    f'This package is unsupported on Python {version.major}.{version.minor}'
    )

# Init
try:
  log.start()
except UserWarning as err:
  std.print_warning(err)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
