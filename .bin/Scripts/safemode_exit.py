# Wizard Kit: Exit SafeMode by editing the BCD

import os
import sys

# STATIC VARIABLES
REG_MSISERVER = r'HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer'

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.common import *
init_global_vars()
os.system('title {}: SafeMode Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
    try:
        os.system('cls')
        print_info('{}: SafeMode Tool\n'.format(KIT_NAME_FULL))
        if not ask('Disable booting to SafeMode?'):
            abort()
        
        # Edit BCD to remove safeboot value
        for boot in ['{current}', '{default}']:
            cmd = ['bcdedit', '/deletevalue', boot, 'safeboot']
            run_program(cmd, check=False)
        
        # Disable MSI access under safemode
        cmd = ['reg', 'delete', REG_MSISERVER, '/f']
        run_program(cmd, check=False)
        
        ## Done ##
        pause('Press Enter to reboot...')
        cmd = ['shutdown', '-r', '-t', '3']
        run_program(cmd, check=False)
        
        # Done
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
