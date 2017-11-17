# Wizard Kit: SFC Tool

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SFC Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()

def abort():
    print_warning('Aborted.')
    pause("Press Enter to exit...")
    exit_script()

if __name__ == '__main__':
    try:
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
            }}
        stay_awake()
        try_and_print(message='SFC scan...', function=run_sfc_scan, other_results=other_results)
        
        # Done
        print_standard('\nDone.')
        pause('Press Enter to exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
