# Wizard Kit: WinPE Root Menu

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.winpe_menus import *
# Fix 7-Zip name
TOOLS['SevenZip'].pop('64')
init_global_vars()
set_title('{}: Root Menu'.format(KIT_NAME_FULL))
set_log_file('WinPE.log')

if __name__ == '__main__':
  try:
    menu_root()
  except SystemExit:
    pass
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
