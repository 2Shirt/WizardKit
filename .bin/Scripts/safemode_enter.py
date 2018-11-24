# Wizard Kit: Enter SafeMode by editing the BCD

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.safemode import *
init_global_vars()
os.system('title {}: SafeMode Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
    try:
        clear_screen()
        print_info('{}: SafeMode Tool\n'.format(KIT_NAME_FULL))
        other_results = {
            'Error': {'CalledProcessError':   'Unknown Error'},
            'Warning': {}}

        if not ask('Enable booting to SafeMode (with Networking)?'):
            abort()

        # Configure SafeMode
        try_and_print(message='Set BCD option...',
            function=enable_safemode, other_results=other_results)
        try_and_print(message='Enable MSI in SafeMode...',
            function=enable_safemode_msi, other_results=other_results)

        # Done
        print_standard('\nDone.')
        pause('Press Enter to reboot...')
        reboot()
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
