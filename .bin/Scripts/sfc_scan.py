# Wizard Kit: SFC Tool

import os
import re

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SFC Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['LogFile'] = '{LogDir}\\SFC.log'.format(**vars_wk)
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('.exe', '64.exe')
os.makedirs(vars_wk['LogDir'], exist_ok=True)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    pause("Press Enter to exit...")
    exit_script()

def exit_script():
    quit()

def run_sfc_scan():
    """Run SFC in a "split window" and report errors."""
    print_info('* Checking system file health', vars_wk['LogFile'])
    _cmd = [
        '{SYSTEMROOT}\\System32\\sfc.exe'.format(**vars_wk['Env']),
        '/scannow']
    _out = run_program(_cmd, check=False, pipe=False)
    # Save stderr
    # with open('{LogDir}\\SFC.err'.format(**vars_wk), 'a') as f:
        # f.write(out.stdout)
    # Save stdout
    # with open('{LogDir}\\SFC.log'.format(**vars_wk), 'a') as f:
        # f.write(out.stdout)

if __name__ == '__main__':
    stay_awake(vars_wk)
    run_sfc_scan()
    
    # Done
    print_standard('\nDone.', vars_wk['LogFile'])
    pause('Press Enter to exit...')
    
    # Open log
    extract_item('Notepad2', vars_wk, silent=True)
    subprocess.Popen([vars_wk['Notepad2'], vars_wk['LogFile']])
    
    # Quit
    kill_process('caffeine.exe')
    exit_script()