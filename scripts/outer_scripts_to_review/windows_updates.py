# Wizard Kit: Windows updates

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.windows_updates import *
init_global_vars()
os.system('title {}: Windows Updates Tool'.format(KIT_NAME_FULL))
set_log_file('Windows Updates Tool.log')

if __name__ == '__main__':
  try:
    clear_screen()
    print_info('{}: Windows Updates Tool\n'.format(KIT_NAME_FULL))

    # Check args
    if '--disable' in sys.argv:
      disable_windows_updates()
    elif '--enable' in sys.argv:
      enable_windows_updates()
    else:
      print_error('Bad mode.')
      abort()

    # Done
    exit_script()
  except GenericError as err:
    # Failed to complete request, show error(s) and prompt tech
    print_standard(' ')
    for line in str(err).splitlines():
      print_warning(line)
    print_standard(' ')
    print_error('Error(s) encountered, see above.')
    print_standard(' ')
    if '--disable' in sys.argv:
      print_standard('Please reboot and try again.')
    pause('Press Enter to exit... ')
    exit_script(1)
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
