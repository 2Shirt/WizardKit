# Wizard Kit: Install the standard SW bundle based on the OS version

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SW Bundle Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\Install SW Bundle.log'.format(**global_vars)

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
        answer_wk_extensions = ask('Install WK Extensions?')
        answer_adobe_reader = ask('Install Adobe Reader?')
        answer_vcr = ask('Install Visual C++ Runtimes?')
        if global_vars['OS']['Version'] in ['7']:
            # Vista is dead, not going to check for it
            answer_mse = ask('Install MSE?')
        else:
            answer_mse = False
        
        if answer_wk_extensions:
            print_info('Installing WK Extensions')
            try_and_print(message='Classic Shell skin...', function=install_classicstart_skin, other_results=other_results)
            try_and_print(message='Google Chrome extensions...', function=install_chrome_extensions)
            try_and_print(message='Mozilla Firefox extensions...', function=install_firefox_extensions)
        print_info('Installing Programs')
        if answer_adobe_reader:
            install_adobe_reader()
        if answer_vcr:
            install_vcredists()
        try_and_print(message='Ninite bundle...', cs='Started', function=install_ninite_bundle, mse=answer_mse)
        print_standard('\nDone.')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
