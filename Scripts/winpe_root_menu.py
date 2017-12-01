# Wizard Kit PE: Root Menu

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.winpe_menus import *
init_global_vars()
set_title('{}: Root Menu'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\WinPE.log'.format(**global_vars)

# STATIC VARIABLES
DISKPART_SCRIPT = r'{}\diskpart.script'.format(global_vars['Env']['TMP'])

if __name__ == '__main__':
    try:
        menu_root()
    except GenericAbort:
        # pause('Press Enter to return to main menu... ')
        pass
    except SystemExit:
        pass
    except:
        major_exception()
