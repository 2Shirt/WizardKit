# Wizard Kit: User Checklist

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: User Checklist Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\User Checklist ({USERNAME}).log'.format(**global_vars, **global_vars['Env'])

def abort():
    print_warning('Aborted.')
    exit_script()

if __name__ == '__main__':
    try:
        stay_awake()
        os.system('cls')
        other_results = {
            'Warning': {
                'NotInstalledError': 'Not installed',
                'NoProfilesError': 'No profiles found',
            }}
        answer_config_browsers =                                ask('Configure Browsers to WK Standards?')
        if answer_config_browsers:
            answer_reset_browsers =                             ask('Reset browsers to safe defaults first?')
        if global_vars['OS']['Version'] == '10':
            answer_config_classicshell =                        ask('Configure ClassicShell to WK Standards?')
            answer_config_explorer_user =                       ask('Configure Explorer to WK Standards?')
        
        # Cleanup
        print_info('Cleanup')
        try_and_print(message='Desktop...',                     function=cleanup_desktop, cs='Done')
        
        # Homepages
        print_info('Current homepages')
        list_homepages()
        
        # Backup
        print_info('Backing up browsers')
        try_and_print(message='Chromium...',                    function=backup_chromium, other_results=other_results)
        try_and_print(message='Google Chrome...',               function=backup_chrome, other_results=other_results)
        try_and_print(message='Google Chrome Canary...',        function=backup_chrome_canary, other_results=other_results)
        try_and_print(message='Internet Explorer...',           function=backup_internet_explorer, other_results=other_results)
        try_and_print(message='Mozilla Firefox (All)...',       function=backup_firefox, other_results=other_results)
        try_and_print(message='Opera...',                       function=backup_opera, other_results=other_results)
        try_and_print(message='Opera Beta...',                  function=backup_opera_beta, other_results=other_results)
        try_and_print(message='Opera Dev...',                   function=backup_opera_dev, other_results=other_results)
        
        # Reset
        if answer_config_browsers and answer_reset_browsers:
            print_info('Resetting browsers')
            try_and_print(message='Internet Explorer...',       function=clean_internet_explorer, cs='Done')
            try_and_print(message='Google Chrome...',           function=reset_google_chrome, other_results=other_results)
            try_and_print(message='Google Chrome Canary...',    function=reset_google_chrome_canary, other_results=other_results)
            try_and_print(message='Mozilla Firefox...',         function=reset_mozilla_firefox, other_results=other_results)
            try_and_print(message='Opera...',                   function=reset_opera, other_results=other_results)
            try_and_print(message='Opera Beta...',              function=reset_opera_beta, other_results=other_results)
            try_and_print(message='Opera Dev...',               function=reset_opera_dev, other_results=other_results)
        
        # Configure
        print_info('Configuring programs')
        if answer_config_browsers:
            try_and_print(message='Internet Explorer...',       function=config_internet_explorer, cs='Done')
            try_and_print(message='Google Chrome...',           function=config_google_chrome, cs='Done', other_results=other_results)
            try_and_print(message='Google Chrome Canary...',    function=config_google_chrome_canary, cs='Done', other_results=other_results)
            try_and_print(message='Mozilla Firefox...',         function=config_mozilla_firefox, cs='Done', other_results=other_results)
            try_and_print(message='Mozilla Firefox Dev...',     function=config_mozilla_firefox_dev, cs='Done', other_results=other_results)
            try_and_print(message='Opera...',                   function=config_opera, cs='Done', other_results=other_results)
            try_and_print(message='Opera Beta...',              function=config_opera_beta, cs='Done', other_results=other_results)
            try_and_print(message='Opera Dev...',               function=config_opera_dev, cs='Done', other_results=other_results)
            try_and_print(message='Set default browser...',     function=set_chrome_as_default, cs='Done', other_results=other_results)
        if global_vars['OS']['Version'] == '10':
            if answer_config_classicshell:
                try_and_print(message='ClassicStart...',        function=config_classicstart, cs='Done')
            if answer_config_explorer_user:
                try_and_print(message='Explorer...',            function=config_explorer_user, cs='Done')
            if not answer_config_browsers and not answer_config_classicshell and not answer_config_explorer_user:
                print_warning('        Skipped')
        else:
            if not answer_config_browsers:
                print_warning('        Skipped')
        
        # Done
        print_standard('\nDone.')
        pause('Press Enter to exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
