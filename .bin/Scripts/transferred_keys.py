# Wizard Kit: Search for product keys in the transfer folder via ProduKey & SW hives

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.product_keys import *
init_global_vars()
os.system('title {}: ProductKey Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\Transferred Keys.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        stay_awake()
        try_and_print(message='Searching for keys...',
            function=list_clientdir_keys, print_return=True)
        
        # Done
        print_standard('\nDone.')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
