# Wizard Kit: DISM wrapper

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: DISM helper Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\DISM helper tool.log'.format(**global_vars)

def abort():
    print_warning('Aborted.')
    exit_script()

if __name__ == '__main__':
    try:
        stay_awake()
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
                'UnsupportedOSError':   'Unsupported OS',
            }}
        options = [
            {'Name': 'Check Health', 'Command': 'Check'},
            {'Name': 'Restore Health', 'Command': 'Restore'}]
        actions = [{'Name': 'Quit', 'Letter': 'Q'}]
        selection = menu_select('Please select action to perform', options, actions)
        os.system('cls')
        print_info('DISM helper tool')
        if selection == 'Q':
            abort()
        elif options[int(selection)-1]['Command'] == 'Check':
            try_and_print(message='DISM ScanHealth...', function=run_dism_scan_health, cs='No corruption', ns='Corruption detected', other_results=other_results)
        elif options[int(selection)-1]['Command'] == 'Restore':
            try_and_print(message='DISM RestoreHealth...', function=run_dism_restore_health, cs='No corruption', ns='Corruption detected', other_results=other_results)
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
