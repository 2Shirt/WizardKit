# Wizard Kit: Check Disk (Fix) Tool

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Check Disk (Fix) Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\Check Disk (Fix).log'.format(**global_vars)

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
        offline_scan = True
        os.system('cls')
        print_info('Check Disk Tool')
        _spotfix = try_and_print(message='CHKDSK Spotfix ({SYSTEMDRIVE})...'.format(**global_vars['Env']), function=run_chkdsk_spotfix, other_results=other_results)
        if global_vars['OS']['Version'] in ['8', '10'] and not _spotfix['CS']:
            offline_scan = ask('Run full offline scan?')
        try_and_print(message='CHKDSK Offline ({SYSTEMDRIVE})...'.format(**global_vars['Env']), function=run_chkdsk_offline, cs='Scheduled',  ns='Error', other_results=other_results)
        
        # Done
        print_success('Done.')
        pause("Press Enter to reboot...")
        run_program(['shutdown', '-r', '-t', '15'], check=False)
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
