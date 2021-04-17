"""Wizard Kit: Auto-Repair Tool"""
# vim: sts=2 sw=2 ts=2

import os
import sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk


if __name__ == '__main__':
  try:
    wk.repairs.win.run_auto_repair()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
