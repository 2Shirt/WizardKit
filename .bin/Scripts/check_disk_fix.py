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
    pause("Press Enter to reboot...")
    run_program('shutdown -r -t 3', check=False)
    quit()

if __name__ == '__main__':
    stay_awake(vars_wk)
    print_info('* Running CHKDSK (repairs) on {SYSTEMDRIVE}'.format(**vars_wk['Env']))
    # Run scan (and attempt to repair errors)
    try:
        if vars_wk['Version'] in ['8', '10']:
            try:
                run_program('chkdsk {SYSTEMDRIVE} /sdcleanup /spotfix'.format(**vars_wk['Env']), pipe=False)
            except subprocess.CalledProcessError:
                print_error('ERROR: CHKDSK is still reporting problems.')
                if ask('Run full offline scan?'):
                    run_program('chkdsk {SYSTEMDRIVE} /offlinescanandfix'.format(**vars_wk['Env']), pipe=False)
        else:
            # Windows 7 and older
            run_program('chkdsk {SYSTEMDRIVE} /F'.format(**vars_wk['Env']), pipe=False)
    except subprocess.CalledProcessError:
        print_error('ERROR: CHKDSK encountered a problem. Please review any messages above.')
        abort()
    
    print_success('Done.')
    kill_process('caffeine.exe')
    exit_script()
