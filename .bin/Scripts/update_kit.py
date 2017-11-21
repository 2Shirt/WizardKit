# Wizard Kit: Download the latest versions of the programs in the kit

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.update import *
init_global_vars()
os.system('title {}: Kit Update Tool'.format(KIT_NAME_FULL))

if __name__ == '__main__':
    try:
        other_results = {
            'Error': {
                'CalledProcessError': 'Unknown Error',
            }}
        stay_awake()
        os.system('cls')
        print_info('Updating Kit Tools')
        
        ## Download ##
        # Data Recovery
        print_info('\nData Recovery')
        try_and_print(message='TestDisk / PhotoRec...', function=update_testdisk, other_results=other_results)
        
        # Data Transfers
        print_info('\nData Transfers')
        try_and_print(message='FastCopy...', function=update_fastcopy, other_results=other_results)
        try_and_print(message='wimlib...', function=update_wimlib, other_results=other_results)
        try_and_print(message='XYplorer...', function=update_xyplorer, other_results=other_results)
        
        # Diagnostics
        print_info('\nDiagnostics')
        try_and_print(message='AIDA64...', function=update_aida64, other_results=other_results)
        try_and_print(message='Autoruns...', function=update_autoruns, other_results=other_results)
        try_and_print(message='BleachBit...', function=update_bleachbit, other_results=other_results)
        try_and_print(message='BlueScreenView...', function=update_bluescreenview, other_results=other_results)
        try_and_print(message='ERUNT...', function=update_erunt, other_results=other_results)
        try_and_print(message='HitmanPro...', function=update_hitmanpro, other_results=other_results)
        try_and_print(message='HWiNFO...', function=update_hwinfo, other_results=other_results)
        try_and_print(message='ProduKey...', function=update_produkey, other_results=other_results)
        
        # Drivers
        print_info('\nDrivers')
        try_and_print(message='Intel RST...', function=update_intel_rst, other_results=other_results)
        try_and_print(message='Intel SSD Toolbox...', function=update_intel_ssd_toolbox, other_results=other_results)
        try_and_print(message='Samsing Magician...', function=update_samsung_magician, other_results=other_results)
        try_and_print(message='Snappy Driver Installer Origin...', function=update_sdi_origin, other_results=other_results)
        
        # Installers
        print_info('\nInstallers')
        try_and_print(message='Adobe Reader DC...', function=update_adobe_reader_dc, other_results=other_results)
        try_and_print(message='MS Office...', function=update_office, other_results=other_results)
        try_and_print(message='Visual C++ Runtimes...', function=update_vcredists, other_results=other_results)
        print_info('\nNinite')
        for section in sorted(NINITE_SOURCES.keys()):
            print_success('    {}'.format(section))
            dest = r'{}\_Ninite\{}'.format(global_vars['CBinDir'], section)
            for name, url in sorted(NINITE_SOURCES[section].items()):
            url = 'https://ninite.com/{}/ninite.exe'.format(url)
                try_and_print(message=name, function=download_generic,
                    other_results=other_results,
                    out_dir=dest, out_name=name, source_url=url)
        
        # Misc
        print_info('\nMisc')
        try_and_print(message='Caffeine...', function=update_caffeine, other_results=other_results)
        try_and_print(message='Classic Start Skin...', function=update_classic_start_skin, other_results=other_results)
        try_and_print(message='Du...', function=update_du, other_results=other_results)
        try_and_print(message='Everything...', function=update_everything, other_results=other_results)
        try_and_print(message='PuTTY...', function=update_putty, other_results=other_results)
        try_and_print(message='Notepad++...', function=update_notepadplusplus, other_results=other_results)
        try_and_print(message='TreeSizeFree...', function=update_treesizefree, other_results=other_results)
        try_and_print(message='XMPlay...', function=update_xmplay, other_results=other_results)
        
        # Repairs
        print_info('\nRepairs')
        try_and_print(message='AdwCleaner...', function=update_adwcleaner, other_results=other_results)
        try_and_print(message='KVRT...', function=update_kvrt, other_results=other_results)
        try_and_print(message='RKill...', function=update_rkill, other_results=other_results)
        try_and_print(message='TDSSKiller...', function=update_tdsskiller, other_results=other_results)
        
        # Uninstallers
        print_info('\nUninstallers')
        try_and_print(message='IObit Uninstaller...', function=update_iobit_uninstaller, other_results=other_results)
        
        # Done
        print_standard('\nDone.')
        pause("Press Enter to exit...")
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
