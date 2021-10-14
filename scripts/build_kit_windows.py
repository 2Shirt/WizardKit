"""WizardKit: Build Kit (Windows)."""
# vim: sts=2 sw=2 ts=2

import os
import sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk # pylint: disable=wrong-import-position


if __name__ == '__main__':
  try:
    wk.kit.build.build_kit()
  except KeyboardInterrupt:
    wk.std.abort()
  except SystemExit:
    raise
  except: #pylint: disable=bare-except
    wk.std.major_exception()
