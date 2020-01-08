#!/usr/bin/env python3
"""Wizard Kit: Hardware Diagnostics"""
# vim: sts=2 sw=2 ts=2

import wk


if __name__ == '__main__':
  try:
    wk.hw.diags.main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
