# Wizard Kit: Install the standard SW bundle based on the OS version

import os
import re

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: SW Bundle Tool')
from functions import *
vars = init_vars()
vars_os = init_vars_os()

if __name__ == '__main__':
    # Adobe Reader
    if vars_os['Version'] != 'Vista':
        print('Installing Adobe Reader DC...')
        _prog = '{BaseDir}/Installers/Extras/Office/Adobe Reader DC.exe'.format(**vars)
        _args = ['/sAll', '/msi', '/norestart', '/quiet', 'ALLUSERS=1', 'EULA_ACCEPT=YES']
        try:
            run_program(_prog, _args)
        except:
            print_error('Failed to install Adobe Reader DC')
    
    # Visual C++ Redists
    print('Installing Visual C++ Runtimes...')
    os.chdir('{BinDir}/_vcredists'.format(**vars))
    _redists = [
        # 2005
        {'Prog':    'msiexec',
         'Args':    ['/i', '2005sp1\\x86\\vcredist.msi', '/qb!', '/norestart']},
        {'Prog':    'msiexec',
         'Args':    ['/i', '2005sp1\\x64\\vcredist.msi', '/qb!', '/norestart']},
        # 2008
        {'Prog':    '2008sp1\\vcredist_x86.exe',
         'Args':    ['/qb! /norestart']},
        {'Prog':    '2008sp1\\vcredist_x64.exe',
         'Args':    ['/qb! /norestart']},
        # 2010
        {'Prog':    '2010\\vcredist_x86.exe',
         'Args':    ['/passive', '/norestart']},
        {'Prog':    '2010\\vcredist_x64.exe',
         'Args':    ['/passive', '/norestart']},
        # 2012
        {'Prog':    '2012u4\\vcredist_x86.exe',
         'Args':    ['/passive', '/norestart']},
        {'Prog':    '2012u4\\vcredist_x64.exe',
         'Args':    ['/passive', '/norestart']},
        # 2013
        {'Prog':    '2013\\vcredist_x86.exe',
         'Args':    ['/install', '/passive', '/norestart']},
        {'Prog':    '2013\\vcredist_x64.exe',
         'Args':    ['/install', '/passive', '/norestart']},
        # 2015
        {'Prog':    '2015u3\\vc_redist.x86.exe',
         'Args':    ['/install', '/passive', '/norestart']},
        {'Prog':    '2015u3\\vc_redist.x64.exe',
         'Args':    ['/install', '/passive', '/norestart']},
    ]
    for vcr in _redists:
        try:
            run_program(vcr['Prog'], vcr['Args'], check=False)
        except:
            print_error('Failed to install {}'.format(vcr['Prog']))
    
    # Main Bundle
    if vars_os['Version'] in ['Vista', '7']:
        # Legacy selection
        if ask('Install MSE?'):
            _prog = '{BaseDir}/Installers/Extras/Security/Microsoft Security Essentials.exe'.format(**vars)
            run_program(_prog, check=False)
        _prog = '{BaseDir}/Installers/Extras/Bundles/Legacy.exe'.format(**vars)
        run_program(_prog, check=False)
    elif vars_os['Version'] in ['8', '10']:
        # Modern selection
        _prog = '{BaseDir}/Installers/Extras/Bundles/Modern.exe'.format(**vars)
        run_program(_prog, check=False)
    
    pause("Press Enter to exit...")
    quit()
