# Wizard Kit: Check or repair component store health via DISM

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.repairs import *
init_global_vars()
os.system('title {}: DISM helper Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\DISM helper tool.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        stay_awake()
        os.system('cls')
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
                'UnsupportedOSError':   'Unsupported OS',
            }}
        options = [
            {'Name': 'Check Health', 'Repair': False},
            {'Name': 'Restore Health', 'Repair': True}]
        actions = [{'Name': 'Quit', 'Letter': 'Q'}]
        selection = menu_select(
            '{}: DISM Menu\n'.format(KIT_NAME_FULL), options, actions)
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
