# Wizard Kit: Copy user data to the system over the network

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Data 1')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\Data 1.log'.format(**global_vars)
global_vars['Data'] = {}

def abort():
    umount_backup_shares()
    print_warning('Aborted.')
    pause("Press Enter to exit...")
    exit_script()

if __name__ == '__main__':
    try:
        # Prep
        stay_awake()
        get_ticket_number()
        os.system('cls')
        select_destination()
        select_backup()
        scan_backup()
        
        # Transfer
        os.system('cls')
        print_info('Transfer Details:\n')
        show_info('Ticket:',        global_vars['TicketNumber'])
        show_info('Source:',        global_vars['Data']['Source'].path)
        show_info('Destination:',   global_vars['Data']['Destination'])
        
        if (not ask('Proceed with transfer?')):
            abort()
        
        print_info('Transferring Data')
        transfer_backup()
        try_and_print(message='Removing extra files...', function=cleanup_transfer, cs='Done')
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
