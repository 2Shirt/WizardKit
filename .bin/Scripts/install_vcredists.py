# Wizard Kit: Install Visual C++ Runtimes

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.setup import *
init_global_vars()
os.system('title {}: Install Visual C++ Runtimes'.format(KIT_NAME_FULL))
set_log_file('Install Visual C++ Runtimes.log')

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    print_info('{}: Install Visual C++ Runtimes\n'.format(KIT_NAME_FULL))
    other_results = {
      'Error': {
        'CalledProcessError':   'Unknown Error',
      }}

    if ask('Install Visual C++ Runtimes?'):
      install_vcredists()
    else:
      abort()

    print_standard('\nDone.')
    exit_script()
  except SystemExit:
    pass
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
