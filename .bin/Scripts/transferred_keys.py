# Wizard Kit: Transferred Keys

import os
import re
import subprocess

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Key Tool')
from functions import *
init_global_vars()
set_global_vars(LogFile='{LogDir}\\Transferred Keys.log'.format(**global_vars))

def abort():
    print_warning('Aborted.')
    exit_script(global_vars)

def extract_keys():
    """Extract keys from provided hives and return a dict."""
    keys = {}
    
    # Extract keys
    extract_item('ProduKey')
    for hive in find_software_hives():
        print_standard('  Scanning {hive}...'.format(hive=hive))
        _args = [
            '/IEKeys', '0',
            '/WindowsKeys', '1',
            '/OfficeKeys', '1',
            '/ExtractEdition', '1',
            '/nosavereg',
            '/regfile', hive,
            '/scomma', '']
        try:
            _out = run_program(global_vars['Tools']['ProduKey'], _args)
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
            print_error('    Failed to extract any keys')
        else:
            for line in _out.stdout.decode().splitlines():
                _match = re.search(r'', line, re.IGNORECASE)
    
    return keys

if __name__ == '__main__':
    stay_awake()
    keys = extract_keys()
    
    # Save Keys
    if keys:
        for product in sorted(keys):
            print_standard('{product}:'.format(product=product))
            for key in sorted(keys[product]):
                print_standard('  {key}'.format(key=key))
    else:
        print_error('No keys found.')
    
    # Done
    print_standard('\nDone.')
    pause("Press Enter to exit...")
    exit_script()
