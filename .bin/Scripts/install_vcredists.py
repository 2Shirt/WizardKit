# Wizard Kit: Install Visual C++ Runtimes

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.setup import *
init_global_vars()
os.system('title {}: Install Visual C++ Runtimes'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\Install Visual C++ Runtimes.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        stay_awake()
        os.system('cls')
        print_info('{}: Install Visual C++ Runtimes\n'.format(KIT_NAME_FULL))
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            }}
        
        if ask('Install Visual C++ Runtimes?'):
            install_vcredists()
        else:
            abort()
        
        print_standard('\nDone.')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
