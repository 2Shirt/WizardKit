# Wizard Kit: Install the standard SW bundle based on the OS version

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.setup import *
init_global_vars()
os.system('title {}: SW Bundle Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\Install SW Bundle.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        stay_awake()
        clear_screen()
        print_info('{}: SW Bundle Tool\n'.format(KIT_NAME_FULL))
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
                'UnsupportedOSError':   'Unsupported OS',
            }}
        answer_extensions = ask('Install Extensions?')
        answer_adobe_reader = ask('Install Adobe Reader?')
        answer_vcr = ask('Install Visual C++ Runtimes?')
        answer_ninite = ask('Install Ninite Bundle?')
        if answer_ninite and global_vars['OS']['Version'] in ['7']:
            # Vista is dead, not going to check for it
            answer_mse = ask('Install MSE?')
        else:
            answer_mse = False
        
        print_info('Installing Programs')
        if answer_adobe_reader:
            install_adobe_reader()
        if answer_vcr:
            install_vcredists()
        if answer_ninite:
            try_and_print(message='Ninite bundle...',
                function=install_ninite_bundle, cs='Started', mse=answer_mse)
        if answer_extensions:
            wait_for_process('ninite.exe')
            print_info('Installing Extensions')
            try_and_print(message='Classic Shell skin...',
                function=install_classicstart_skin,
                other_results=other_results)
            try_and_print(message='Google Chrome extensions...',
                function=install_chrome_extensions)
            try_and_print(message='Mozilla Firefox extensions...',
                function=install_firefox_extensions)
        print_standard('\nDone.')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
