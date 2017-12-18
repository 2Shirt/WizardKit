# Wizard Kit: Copy user data to the system from a local or network source

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.data import *
from functions.repairs import *
init_global_vars()
os.system('title {}: User Data Transfer Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\User Data Transfer.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        # Prep
        stay_awake()
        clear_screen()
        print_info('{}: User Data Transfer Tool\n'.format(KIT_NAME_FULL))
        ticket_number = get_ticket_number()
        folder_path = r'{}\Transfer'.format(KIT_NAME_SHORT)
        dest = select_destination(folder_path=folder_path,
            prompt='Which disk are we transferring to?')
        source = select_source(ticket_number)
        items = scan_source(source, dest)
        
        # Transfer
        clear_screen()
        print_info('Transfer Details:\n')
        show_info('Ticket:',        ticket_number)
        show_info('Source:',        source.path)
        show_info('Destination:',   dest)
        
        if (not ask('Proceed with transfer?')):
            umount_backup_shares()
            abort()
        
        print_info('Transferring Data')
        transfer_source(source, dest, items)
        try_and_print(message='Removing extra files...',
            function=cleanup_transfer, cs='Done', dest_path=dest)
        umount_backup_shares()
        
        # Done
        run_kvrt()
        print_standard('\nDone.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
