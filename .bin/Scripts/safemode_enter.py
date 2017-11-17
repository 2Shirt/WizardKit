# Wizard Kit: Enter SafeMode by editing the BCD

import os

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SafeMode Tool')
from functions import *

if __name__ == '__main__':
    if ask('Enable booting to SafeMode (with Networking)?'):
        # Edit BCD to set safeboot as default
        run_program('bcdedit /set {default} safeboot network', check=False)
        
        # Enable MSI access under safemode
        run_program(r'reg add HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer /f', check=False)
        run_program(r'reg add HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer /ve /t REG_SZ /d "Service" /f', check=False)
    
        ## Done ##
        pause('Press Enter to reboot...')
        run_program('shutdown -r -t 3', check=False)
    
    # Quit
    quit()
