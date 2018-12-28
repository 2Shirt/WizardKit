# Wizard Kit: Check, and possibly repair, system file health via SFC

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.repairs import *
init_global_vars()
os.system('title {}: SFC Tool'.format(KIT_NAME_FULL))
set_log_file('SFC Tool.log')

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    print_info('{}: SFC Tool\n'.format(KIT_NAME_FULL))
    other_results = {
      'Error': {
        'CalledProcessError':   'Unknown Error',
      },
      'Warning': {
        'GenericRepair':    'Repaired',
      }}
    if ask('Run a SFC scan now?'):
      try_and_print(message='SFC scan...',
        function=run_sfc_scan, other_results=other_results)
    else:
      abort()

    # Done
    print_standard('\nDone.')
    pause('Press Enter to exit...')
    exit_script()
  except SystemExit:
    pass
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
