# Wizard Kit: Transferred Keys

import os
import re
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Key Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['LogFile'] = '{LogDir}\\Transferred Keys.log'.format(**vars_wk)
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
vars_wk['ProduKey'] = '{BinDir}\\ProduKey\\ProduKey.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('.exe', '64.exe')
    vars_wk['ProduKey'] = vars_wk['ProduKey'].replace('.exe', '64.exe')
os.makedirs(vars_wk['LogDir'], exist_ok=True)
REGEX_DIR = re.compile(r'^(config$|RegBack$|System32$|Transfer|Win)', re.IGNORECASE)
REGEX_FILE = re.compile(r'^Software$', re.IGNORECASE)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

def exit_script():
    pause("Press Enter to exit...")
    quit()

def find_hives():
    """Search for transferred SW hives and return a list."""
    hives = []
    search_paths = [vars_wk['ClientDir']]
    
    while len(search_paths) > 0:
        for item in os.scandir(search_paths.pop(0)):
            if item.is_dir() and REGEX_DIR.search(item.name):
                search_paths.append(item.path)
            if item.is_file() and REGEX_FILE.search(item.name):
                hives.append(item.path)
    
    return hives

def extract_keys(hives=None):
    """Extract keys from provided hives and return a dict."""
    keys = {}
    
    # Bail early
    if hives is None:
        print_error('  ERROR: No hives found.')
        abort()
    
    # Extract keys
    extract_item('ProduKey', vars_wk)
    for hive in hives:
        print_standard('  Scanning {hive}...'.format(hive=hive), vars_wk['LogFile'])
        _args = [
            '/IEKeys', '0',
            '/WindowsKeys', '1',
            '/OfficeKeys', '1',
            '/ExtractEdition', '1',
            '/nosavereg',
            '/regfile', hive,
            '/scomma', '']
        try:
            _out = run_program(vars_wk['ProduKey'], _args)
            for line in _out.stdout.decode().splitlines():
                # Add key to keys under product only if unique
                _tmp = line.split(',')
                _product = _tmp[0]
                _key = _tmp[2]
                if _product not in keys:
                    keys[_product] = []
                if _key not in keys[_product]:
                    keys[_product].append(_key)
        except subprocess.CalledProcessError:
            print_error('    Failed to extract any keys', vars_wk['LogFile'])
        else:
            for line in _out.stdout.decode().splitlines():
                _match = re.search(r'', line, re.IGNORECASE)
    
    return keys

if __name__ == '__main__':
    stay_awake(vars_wk)
    hives = find_hives()
    keys = extract_keys(hives)
    
    # Save Keys
    if keys:
        for product in sorted(keys):
            print_standard('{product}:'.format(product=product), vars_wk['LogFile'])
            for key in sorted(keys[product]):
                print_standard('  {key}'.format(key=key), vars_wk['LogFile'])
    else:
        print_error('No keys found.', vars_wk['LogFile'])
    
    # Open log
    extract_item('Notepad2', vars_wk, silent=True)
    subprocess.Popen([vars_wk['Notepad2'], vars_wk['LogFile']])
    
    # Quit
    kill_process('caffeine.exe')
    exit_script()