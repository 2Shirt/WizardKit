# Wizard Kit: Activate Windows using various methods

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.activation import *
init_global_vars()
os.system('title {}: Windows Activation Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
    try:
        stay_awake()
        clear_screen()
        print_info('{}: Windows Activation Tool\n'.format(KIT_NAME_FULL))
        # Bail early if already activated
        if windows_is_activated():
            print_info('This system is already activated')
            sleep(5)
            exit_script()
        other_results = {
            'Error': {
                'BIOSKeyNotFoundError':   'BIOS key not found.',
            }}

        # Determine activation method
        activation_methods = [
            {'Name': 'Activate with BIOS key', 'Function': activate_with_bios},
            ]
        if global_vars['OS']['Version'] not in ('8', '8.1', '10'):
            activation_methods[0]['Disabled'] = True
        actions = [
            {'Name': 'Quit', 'Letter': 'Q'},
            ]

        while True:
            selection = menu_select(
                '{}: Windows Activation Menu'.format(KIT_NAME_FULL),
                main_entries=activation_methods, action_entries=actions)

            if (selection.isnumeric()):
                result = try_and_print(
                    message = activation_methods[int(selection)-1]['Name'],
                    function = activation_methods[int(selection)-1]['Function'],
                    other_results=other_results)
                if result['CS']:
                    break
                else:
                    sleep(2)
            elif selection == 'Q':
                exit_script()

        # Done
        print_success('\nDone.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
