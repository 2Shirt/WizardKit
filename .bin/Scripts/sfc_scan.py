# Wizard Kit: Check, and possibly repair, system file health via SFC

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.repairs import *
init_global_vars()
os.system('title {}: SFC Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\SFC Tool.log'.format(**global_vars)

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
        try_and_print(message='SFC scan...',
            function=run_sfc_scan, other_results=other_results)
        
        # Done
        print_standard('\nDone.')
        pause('Press Enter to exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
