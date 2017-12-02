# Wizard Kit: WinPE Root Menu

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.winpe_menus import *
init_global_vars()
set_title('{}: Root Menu'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\WinPE.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        menu_root()
    except SystemExit:
        pass
    except:
        major_exception()
