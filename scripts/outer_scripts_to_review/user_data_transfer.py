# Wizard Kit: Copy user data to the system from a local or network source

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.data import *
from functions.repairs import *
init_global_vars()
os.system('title {}: User Data Transfer Tool'.format(KIT_NAME_FULL))
set_log_file('User Data Transfer.log')

if __name__ == '__main__':
  try:
    # Prep
    stay_awake()
    clear_screen()
    print_info('{}: User Data Transfer Tool\n'.format(KIT_NAME_FULL))

    # Get backup name prefix
    ticket_number = get_ticket_number()
    if ENABLED_TICKET_NUMBERS:
      backup_prefix = ticket_number
    else:
      backup_prefix = get_simple_string(prompt='Enter backup name prefix')
      backup_prefix = backup_prefix.replace(' ', '_')

    # Set destination
    folder_path = r'{}\Transfer'.format(KIT_NAME_SHORT)
    dest = select_destination(folder_path=folder_path,
      prompt='Which disk are we transferring to?')

    # Set source items
    source = select_source(backup_prefix)
    items = scan_source(source, dest)

    # Transfer
    clear_screen()
    print_info('Transfer Details:\n')
    if ENABLED_TICKET_NUMBERS:
      show_data('Ticket:',    ticket_number)
    show_data('Source:',    source.path)
    show_data('Destination:',   dest)

    if (not ask('Proceed with transfer?')):
      umount_backup_shares()
      abort()

    print_info('Transferring Data')
    transfer_source(source, dest, items)
    try_and_print(message='Removing extra files...',
      function=cleanup_transfer, cs='Done', dest_path=dest)
    umount_backup_shares()

    # Done
    try_and_print(message='Running KVRT...',
      function=run_kvrt, cs='Started')
    print_standard('\nDone.')
    pause("Press Enter to exit...")
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
