# Wizard Kit: System Checklist

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.cleanup import *
from functions.diags import *
from functions.info import *
from functions.product_keys import *
from functions.setup import *
init_global_vars()
os.system('title {}: System Checklist Tool'.format(KIT_NAME_FULL))
global_vars['LogFile'] = r'{LogDir}\System Checklist.log'.format(**global_vars)

if __name__ == '__main__':
    try:
        stay_awake()
        ticket_number = get_ticket_number()
        os.system('cls')
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
                'BIOSKeyNotFoundError': 'BIOS key not found',
            },
            'Warning': {}}
        print_info('Starting System Checklist for Ticket #{}\n'.format(
            ticket_number))

        # Configure
        print_info('Configure')
        if global_vars['OS']['Version'] == '10':
            try_and_print(message='Explorer...',
                function=config_explorer_system, cs='Done')
        try_and_print(message='Updating Clock...',
            function=update_clock, cs='Done')

        # Cleanup
        print_info('Cleanup')
        try_and_print(message='Desktop...',
            function=cleanup_desktop, cs='Done')
        try_and_print(message='AdwCleaner...',
            function=cleanup_adwcleaner, cs='Done')

        # Export system info
        print_info('Backup System Information')
        try_and_print(message='AIDA64 reports...',
            function=run_aida64, cs='Done')
        try_and_print(message='File listing...',
            function=backup_file_list, cs='Done')
        try_and_print(message='Power plans...',
            function=backup_power_plans, cs='Done')
        try_and_print(message='Product Keys...',
            function=run_produkey, cs='Done')
        try_and_print(message='Registry...',
            function=backup_registry, cs='Done')

        # User data
        print_info('User Data')
        show_user_data_summary()

        # Summary
        print_info('Summary')
        try_and_print(message='Operating System:',
            function=show_os_name, ns='Unknown', silent_function=False)
        try_and_print(message='Activation:',
            function=show_os_activation, ns='Unknown', silent_function=False)
        if (not windows_is_activated()
            and global_vars['OS']['Version'] in ('8', '10')):
            try_and_print(message='BIOS Activation:',
                function=activate_windows_with_bios,
                other_results=other_results)
        try_and_print(message='Installed Office:',
            function=get_installed_office, ns='Unknown', print_return=True)
        show_free_space()
        try_and_print(message='Installed RAM:',
            function=show_installed_ram, ns='Unknown', silent_function=False)

        # Upload info
        if ENABLED_UPLOAD_DATA:
            print_info('Finalizing')
            try_and_print(message='Compressing Info...',
                function=compress_info, cs='Done')
            try_and_print(message='Uploading to NAS...',
                function=upload_info, cs='Done')

        # Play audio, show devices, open Windows updates, and open Activation
        popen_program(['mmc', 'devmgmt.msc'])
        run_hwinfo_sensors()
        popen_program(['control', '/name', 'Microsoft.WindowsUpdate'])
        if not windows_is_activated():
            popen_program('slui')
        sleep(3)
        run_xmplay()

        # Done
        print_standard('\nDone.')
        pause('Press Enter exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
