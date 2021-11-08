"""WizardKit: Embedded Python helper.

This saves the keystrokes needed to fix the path and import wk. To use:
python.exe -i embedded_python_env.py
"""
# vim: sts=2 sw=2 ts=2

import os
import sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
import wk # pylint: disable=wrong-import-position
wk.std.print_colored(
  (wk.cfg.main.KIT_NAME_FULL, ': ', 'Debug Console'),
  ('GREEN', None, 'YELLOW'),
  sep='',
  )
print('')
