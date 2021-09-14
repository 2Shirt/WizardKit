"""WizardKit: wk module init"""
# vim: sts=2 sw=2 ts=2

from sys import version_info as version

from . import cfg
from . import debug
from . import exe
from . import graph
from . import hw
from . import io
from . import kit
from . import log
from . import net
from . import os
from . import repairs
from . import setup
from . import std
from . import tmux


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
