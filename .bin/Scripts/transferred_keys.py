# Wizard Kit: Transferred Keys

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: ProductKey Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\Transferred Keys.log'.format(**global_vars)

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
                'GenericError':         'No keys found',
            }}
        stay_awake()
        try_and_print(message='Extracting keys...', function=extract_keys, other_results=other_results)
        try_and_print(message='Displaying keys...', function=save_keys, print_return=True)
        
        # Done
        print_standard('\nDone.')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
