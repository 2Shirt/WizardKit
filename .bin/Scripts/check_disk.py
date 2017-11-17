# Wizard Kit: Check Disk Tool

import os

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Check Disk Tool')
from functions import *
init_global_vars()
set_global_vars(LogFile='{LogDir}\\Check Disk.log'.format(**global_vars))

def abort():
    print_warning('Aborted.', global_vars['LogFile'])
    exit_script()

if __name__ == '__main__':
    stay_awake()
    other_results = {
        'Error': {
            'CalledProcessError':   'Unknown Error',
        },
        'Warning': {
            'GenericRepair':        'Repaired',
            'UnsupportedOSError':   'Unsupported OS',
        }}
    os.system('cls')
    print_info('Check Disk Tool')
    try_and_print(message='CHKDSK ({SYSTEMDRIVE})...'.format(**global_vars['Env']), function=run_chkdsk, cs='CS',  ns='NS', other_results=other_results)
    
    # Done
    print_success('Done.')
    pause("Press Enter to exit...")
    exit_script()
