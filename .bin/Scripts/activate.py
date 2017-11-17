# Wizard Kit: Activate Windows using various methods

import csv
import os
import re
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Windows Activation Tool')
from functions import *
vars = init_vars()
vars_os = init_vars_os()
vars['ProduKey'] = '{BinDir}\\tmp\\ProduKey.exe'.format(**vars)
vars['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars)
if vars_os['Arch'] == 64:
    vars['SevenZip'] = vars['SevenZip'].replace('7za.exe', '7za64.exe')
    vars['ProduKey'] = vars['ProduKey'].replace('ProduKey.exe', 'ProduKey64.exe')

def abort():
    print_warning('Aborted.')
    exit_script()

def exit_script():
    pause("Press Enter to exit...")
    quit()

def extract_produkey():
    """Extract ProduKey and remove stale configuration file(s)."""
    lolwut = run_program(vars['SevenZip'], ['e', '{BinDir}\\ProduKey.7z'.format(**vars), '-o{TmpDir}'.format(**vars), '-pAbracadabra', '-aoa', '-bsp0', '-bso0'], check=False)
    _cwd = os.getcwd()
    os.chdir('{TmpDir}'.format(**vars))
    for _f in ['ProduKey.cfg', 'ProduKey64.cfg']:
        try:
            os.remove(_f)
        except FileNotFoundError:
            pass
    os.chdir(_cwd)

def activate_with_bios():
    """Attempt to activate Windows with a key stored in the BIOS."""
    extract_produkey()
    _args = [
        '/nosavereg',
        '/scomma', '{TmpDir}\\keys.csv'.format(**vars),
        '/WindowsKeys', '1',
        '/OfficeKeys', '0',
        '/IEKeys', '0',
        '/SQLKeys', '0',
        '/ExchangeKeys', '0']
    try:
        run_program(vars['ProduKey'], _args, pipe=False)
        with open ('{TmpDir}\\keys.csv'.format(**vars), newline='') as key_file:
            key_reader = csv.reader(key_file)
            _key_found = False
            for key in key_reader:
                if 'BIOS' in key[0] and re.match(r'^\w{5}-\w{5}-\w{5}-\w{5}-\w{5}$', key[2]):
                    _key_found = True
                    print_standard('BIOS key found, installing...')
                    run_program('cscript {WINDIR}\\System32\\slmgr.vbs /ipk {pkey} //nologo'.format(**vars['Env'], pkey=key[2]), check=False, shell=True)
                    sleep(15)
                    print_standard('Attempting activation...')
                    run_program('cscript {WINDIR}\\System32\\slmgr.vbs /ato //nologo'.format(**vars['Env']), check=False, shell=True)
                    sleep(15)
                    # Open system properties for user verification
                    subprocess.Popen(['control', 'system'])
                    break
            if not _key_found:
                print_error('ERROR: BIOS not key found.')
                abort()
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to extract BIOS key')
        abort()

def activate_with_hive():
    """Scan any transferred software hives for Windows keys and attempt activation."""
    # extract_produkey()
    pass

if __name__ == '__main__':
    # Bail early if already activated
    if 'The machine is permanently activated.' in vars_os['Activation']:
        print_info('This system is already activated')
        # exit_script()
    
    # Determine activation method
    activation_methods = [
        {'Name': 'Activate with BIOS key', 'Function': activate_with_bios},
        {'Name': 'Activate with transferred SW hive', 'Function': activate_with_hive, 'Disabled': True},
        ]
    if not re.match(r'^(8|10)$', vars_os['Version']):
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
    exit_script()