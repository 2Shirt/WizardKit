# Wizard Kit: Copy user data to the system over the network

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.cleanup import *
from functions.data import *
init_global_vars()
os.system('title {}: CBS Cleanup'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\CBS Cleanup.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        # Prep
        stay_awake()
        get_ticket_number()
        os.system('cls')
        folder_path = r'{}\Backups'.format(KIT_NAME_SHORT)
        dest = select_destination(folder_path=folder_path,
            prompt='Which disk are we using for temp data and backup?')
        if (not ask('Proceed with CBS cleanup?')):
            abort()
        
        # Run Cleanup
        try_and_print(message='Running cleanup...', function=cleanup_cbs,
            cs='Done', dest_folder=dest)
        
        # Done
        print_standard('\nDone.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
