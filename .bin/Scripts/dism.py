# Wizard Kit: Check or repair component store health via DISM

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.repairs import *
init_global_vars()
os.system('title {}: DISM helper Tool'.format(KIT_NAME_FULL))
set_log_file('DISM Helper.log')

if __name__ == '__main__':
    try:
        stay_awake()
        clear_screen()
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
                'UnsupportedOSError':   'Unsupported OS',
            }}
        disabled = bool(global_vars['OS']['Version'] not in ('8', '8.1', '10'))
        options = [
            {'Name': 'Check Health', 'Repair': False, 'Disabled': disabled},
            {'Name': 'Restore Health', 'Repair': True, 'Disabled': disabled}]
        actions = [{'Name': 'Quit', 'Letter': 'Q'}]
        selection = menu_select(
            '{}: DISM Menu\n'.format(KIT_NAME_FULL),
            main_entries=options,
            action_entries=actions)
        print_info('{}: DISM Menu\n'.format(KIT_NAME_FULL))
        if selection == 'Q':
            abort()
        elif selection.isnumeric():
            repair = options[int(selection)-1]['Repair']
            if repair:
                message='DISM RestoreHealth...'
            else:
                message='DISM ScanHealth...'
            try_and_print(message=message, function=run_dism,
                cs='No corruption', ns='Corruption detected',
                other_results=other_results, repair=repair)
        else:
            abort()

        # Done
        print_success('Done.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
