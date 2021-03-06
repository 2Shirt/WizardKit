#!/usr/bin/env python3
"""Wizard Kit: ddrescue TUI"""
# vim: sts=2 sw=2 ts=2

import wk

from docopt import docopt


if __name__ == '__main__':
  try:
    docopt(wk.hw.ddrescue.DOCSTRING)
  except SystemExit:
    print('')
    wk.std.pause('Press Enter to exit...')
    raise

  try:
    wk.hw.ddrescue.main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
