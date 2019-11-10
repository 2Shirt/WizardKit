#!/usr/bin/env python3
"""Wizard Kit: Hardware Diagnostics"""
# vim: sts=2 sw=2 ts=2

import wk


def main():
  """Run hardware diagnostics."""
  state = wk.hw.diags.State()
  wk.hw.diags.main_menu()


if __name__ == '__main__':
  try:
    main()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
