# Wizard Kit: Activate Windows using various methods

import csv
import os
import re
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Windows Activation Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['ProduKey'] = '{BinDir}\\ProduKey\\ProduKey.exe'.format(**vars_wk)
vars_wk['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['SevenZip'] = vars_wk['SevenZip'].replace('7za.exe', '7za64.exe')
    vars_wk['ProduKey'] = vars_wk['ProduKey'].replace('ProduKey.exe', 'ProduKey64.exe')

def abort():
    print_warning('Aborted.')
    exit_script()

def activate_with_bios():
    """Attempt to activate Windows with a key stored in the BIOS."""
    extract_item('ProduKey', vars_wk, silent=True)
    _args = [
        '/nosavereg',
        '/scomma', '{TmpDir}\\keys.csv'.format(**vars_wk),
        '/WindowsKeys', '1',
        '/OfficeKeys', '0',
        '/IEKeys', '0',
        '/SQLKeys', '0',
        '/ExchangeKeys', '0']
    try:
        run_program(vars_wk['ProduKey'], _args, pipe=False)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to extract BIOS key')
        abort()
    else:
        with open ('{TmpDir}\\keys.csv'.format(**vars_wk), newline='') as key_file:
            key_reader = csv.reader(key_file)
            _key_found = False
            for key in key_reader:
                if 'BIOS' in key[0] and re.match(r'^\w{5}-\w{5}-\w{5}-\w{5}-\w{5}$', key[2]):
                    _key_found = True
                    print_standard('BIOS key found, installing...')
                    run_program('cscript {SYSTEMROOT}\\System32\\slmgr.vbs /ipk {pkey} //nologo'.format(**vars_wk['Env'], pkey=key[2]), check=False, shell=True)
                    sleep(15)
                    print_standard('Attempting activation...')
                    run_program('cscript {SYSTEMROOT}\\System32\\slmgr.vbs /ato //nologo'.format(**vars_wk['Env']), check=False, shell=True)
                    sleep(15)
                    # Open system properties for user verification
                    subprocess.Popen(['control', 'system'])
                    break
            if not _key_found:
                print_error('ERROR: BIOS not key found.')
                abort()

def activate_with_hive():
    """Scan any transferred software hives for Windows keys and attempt activation."""
    extract_item('ProduKey', vars_wk, silent=True)

def exit_script():
    pause("Press Enter to exit...")
    quit()

def is_activated():
    """Updates activation status, checks if activated, and returns a bool."""
    _out = run_program('cscript /nologo {SYSTEMROOT}\\System32\\slmgr.vbs /xpr'.format(**vars_wk['Env']))
    _out = _out.stdout.decode().splitlines()
    _out = [l for l in _out if re.match(r'^\s', l)]
    if len(_out) > 0:
        vars_wk['Activation'] = re.sub(r'^\s+', '', _out[0])
    else:
        vars_wk['Activation'] = 'Activation status unknown'
    return 'The machine is permanently activated.' in vars_wk['Activation']

if __name__ == '__main__':
    stay_awake(vars_wk)
    # Bail early if already activated
    if is_activated():
        print_info('This system is already activated')
        exit_script()
    
    # Determine activation method
    activation_methods = [
        {'Name': 'Activate with BIOS key', 'Function': activate_with_bios},
        {'Name': 'Activate with transferred SW hive', 'Function': activate_with_hive, 'Disabled': True},
        ]
    if not re.match(r'^(8|10)$', vars_wk['Version']):
        activation_methods[0]['Disabled'] = True
    actions = [
        {'Name': 'Quit', 'Letter': 'Q'},
        ]
    
    # Main loop
    while True:
        selection = menu_select('Wizard Kit: Windows Activation Menu', activation_methods, actions)

        if (selection.isnumeric()):
            activation_methods[int(selection)-1]['Function']()
            break
        elif selection == 'Q':
            exit_script()
    
    # Quit
    print_success('Done.')
    kill_process('caffeine.exe')
    exit_script()