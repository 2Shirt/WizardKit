# Wizard Kit: Enter SafeMode by editing the BCD

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
        clear_screen()
        print_info('{}: SafeMode Tool\n'.format(KIT_NAME_FULL))
        if not ask('Enable booting to SafeMode (with Networking)?'):
            abort()
        
        # Edit BCD to set safeboot as default
        cmd = ['bcdedit', '/set', '{default}', 'safeboot', 'network']
        run_program(cmd, check=False)
        
        # Enable MSI access under safemode
        cmd = ['reg', 'add', REG_MSISERVER, '/f']
        run_program(cmd, check=False)
        cmd = ['reg', 'add', REG_MSISERVER, '/ve',
                '/t', 'REG_SZ', '/d', 'Service', '/f']
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
