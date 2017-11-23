# Wizard Kit: Check or repair the %SYSTEMDRIVE% filesystem via CHKDSK

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.repairs import *
init_global_vars()
os.system('title {}: Check Disk Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\Check Disk.log'.format(**global_vars)

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
            {'Name': 'Run CHKDSK scan (read-only)', 'Repair': False},
            {'Name': 'Schedule CHKDSK scan (offline repair)', 'Repair': True}]
        actions = [{'Name': 'Quit', 'Letter': 'Q'}]
        selection = menu_select(
            '{}: Check Disk Menu\n'.format(KIT_NAME_FULL), options, actions)
        print_info('{}: Check Disk Menu\n'.format(KIT_NAME_FULL))
        if selection == 'Q':
            abort()
        elif selection.isnumeric():
            repair = options[int(selection)-1]['Repair']
            if repair:
                cs = 'Scheduled'
            else:
                cs = 'CS'
            message = 'CHKDSK ({SYSTEMDRIVE})...'.format(**global_vars['Env'])
            try_and_print(message=message, function=run_chkdsk,
                cs=cs, other_results=other_results, repair=repair)
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
