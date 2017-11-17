# Wizard Kit: Activate Windows using various methods

import os
import re
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Windows Activation Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()

def abort():
    print_warning('Aborted.')
    exit_script()

def activate_with_bios():
    """Attempt to activate Windows with a key stored in the BIOS."""
    try_and_print(message='BIOS Activation:',   function=activate_windows_with_bios, other_results=other_results)

if __name__ == '__main__':
    try:
        stay_awake()
        # Bail early if already activated
        if windows_is_activated():
            print_info('This system is already activated')
            exit_script()

        # Determine activation method
        activation_methods = [
            {'Name': 'Activate with BIOS key', 'Function': activate_with_bios},
            ]
        if not re.match(r'^(8|10)$', global_vars['OS']['Version']):
            activation_methods[0]['Disabled'] = True
        actions = [
            {'Name': 'Quit', 'Letter': 'Q'},
            ]

        # Main loop
        while True:
            selection = menu_select('Wizard Kit: Windows Activation Menu', activation_methods, actions)

            if (selection.isnumeric()):
                activation_methods[int(selection)-1]['Function']()
                break
            elif selection == 'Q':
                exit_script()

        # Done
        print_success('Done.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
