# Wizard Kit: Backup CBS Logs and prep CBS temp data for deletion

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.cleanup import *
from functions.data import *
init_global_vars()
os.system('title {}: CBS Cleanup'.format(KIT_NAME_FULL))
set_log_file('CBS Cleanup.log')

if __name__ == '__main__':
  try:
    # Prep
    stay_awake()
    clear_screen()
    folder_path = r'{}\Backups'.format(KIT_NAME_SHORT)
    dest = select_destination(folder_path=folder_path,
      prompt='Which disk are we using for temp data and backup?')

    # Show details
    print_info('{}: CBS Cleanup Tool\n'.format(KIT_NAME_FULL))
    show_data('Backup / Temp path:', dest)
    print_standard('\n')
    if (not ask('Proceed with CBS cleanup?')):
      abort()

    # Run Cleanup
    try_and_print(message='Running cleanup...', function=cleanup_cbs,
      cs='Done', dest_folder=dest)

    # Done
    print_standard('\nDone.')
    pause("Press Enter to exit...")
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
