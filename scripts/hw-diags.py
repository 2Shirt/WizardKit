#!/usr/bin/env python3
"""WizardKit: Hardware Diagnostics"""
# pylint: disable=invalid-name
# vim: sts=2 sw=2 ts=2

from docopt import docopt

import wk


if __name__ == '__main__':
  try:
    docopt(wk.hw.diags.DOCSTRING)
  except SystemExit:
    print('')
    wk.std.pause('Press Enter to exit...')
    raise

  try:
    wk.hw.diags.main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
