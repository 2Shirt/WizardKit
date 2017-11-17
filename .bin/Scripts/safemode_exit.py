# Wizard Kit: Exit SafeMode by editing the BCD

import os

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SafeMode Tool')
from functions import *

if __name__ == '__main__':
    if ask('Disable booting to SafeMode?'):
        # Edit BCD to remove safeboot value
        run_program('bcdedit /deletevalue {current} safeboot', check=False)
        run_program('bcdedit /deletevalue {default} safeboot', check=False)
        
        # Disable MSI access under safemode
        run_program(r'reg delete HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer /f', check=False)
    
        ## Done ##
        pause('Press Enter to reboot...')
        run_program('shutdown -r -t 3', check=False)
    
    # Quit
    quit()