# Wizard Kit: Check Disk Tool

import os
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Check Disk Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

def exit_script():
    pause("Press Enter to exit...")
    quit()

if __name__ == '__main__':
    stay_awake(vars_wk)
    print_info('* Running CHKDSK (read-only) on {SYSTEMDRIVE}'.format(**vars_wk['Env']))
    # Run scan (read-only)
    try:
        if vars_wk['Version'] in ['8', '10']:
            run_program('chkdsk {SYSTEMDRIVE} /scan /pref'.format(**vars_wk['Env']), pipe=False)
        else:
            # Windows 7 and older
            run_program('chkdsk {SYSTEMDRIVE}'.format(**vars_wk['Env']), pipe=False)
    except subprocess.CalledProcessError:
        print_error('ERROR: CHKDSK encountered a problem. Please review any messages above.')
        abort()
    
    print_success('Done.')
    kill_process('caffeine.exe')
    exit_script()
