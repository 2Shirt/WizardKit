# Wizard Kit: System Checklist

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.activation import *
from functions.cleanup import *
from functions.diags import *
from functions.info import *
from functions.product_keys import *
from functions.setup import *
init_global_vars()
os.system('title {}: System Checklist Tool'.format(KIT_NAME_FULL))
set_log_file('System Checklist.log')

if __name__ == '__main__':
    try:
        stay_awake()
        clear_screen()
        print_info('{}: System Checklist Tool\n'.format(KIT_NAME_FULL))
        ticket_number = get_ticket_number()
        other_results = {
            'Error': {
                'BIOSKeyNotFoundError':     'BIOS key not found',
                'CalledProcessError':       'Unknown Error',
                'FileNotFoundError':        'File not found',
                'GenericError':             'Unknown Error',
                'SecureBootDisabledError':  'Disabled',
            },
            'Warning': {
                'OSInstalledLegacyError':   'OS installed Legacy',
                'SecureBootNotAvailError':  'Not available',
                'SecureBootUnknownError':   'Unknown',
            }}
        if ENABLED_TICKET_NUMBERS:
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
        try_and_print(message='AdwCleaner...',
            function=cleanup_adwcleaner, cs='Done', other_results=other_results)
        try_and_print(message='Desktop...',
            function=cleanup_desktop, cs='Done')
        try_and_print(message='{}...'.format(KIT_NAME_FULL),
            function=delete_empty_folders, cs='Done',
            folder_path=global_vars['ClientDir'])

        # Export system info
        print_info('Backup System Information')
        try_and_print(message='AIDA64 reports...',
            function=run_aida64, cs='Done', other_results=other_results)
        try_and_print(message='File listing...',
            function=backup_file_list, cs='Done', other_results=other_results)
        try_and_print(message='Power plans...',
            function=backup_power_plans, cs='Done')
        try_and_print(message='Product Keys...', other_results=other_results,
            function=run_produkey, cs='Done')
        try_and_print(message='Registry...',
            function=backup_registry, cs='Done', other_results=other_results)

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
            and global_vars['OS']['Version'] in ('8', '8.1', '10')):
            try_and_print(message='BIOS Activation:',
                function=activate_with_bios,
                other_results=other_results)
        try_and_print(message='Secure Boot Status:',
            function=check_secure_boot_status, other_results=other_results)
        try_and_print(message='Installed RAM:',
            function=show_installed_ram, ns='Unknown', silent_function=False)
        show_free_space()
        try_and_print(message='Installed Antivirus:',
            function=get_installed_antivirus, ns='Unknown',
            other_results=other_results, print_return=True)
        try_and_print(message='Installed Office:',
            function=get_installed_office, ns='Unknown',
            other_results=other_results, print_return=True)

        # Play audio, show devices, open Windows updates, and open Activation
        try_and_print(message='Opening Device Manager...',
            function=open_device_manager, cs='Started')
        try_and_print(message='Opening HWiNFO (Sensors)...',
            function=run_hwinfo_sensors, cs='Started', other_results=other_results)
        try_and_print(message='Opening Windows Updates...',
            function=open_windows_updates, cs='Started')
        if not windows_is_activated():
            try_and_print(message='Opening Windows Activation...',
                function=open_windows_activation, cs='Started')
        sleep(3)
        try_and_print(message='Running XMPlay...',
            function=run_xmplay, cs='Started', other_results=other_results)
        try:
            check_secure_boot_status(show_alert=True)
        except:
            # Only trying to open alert message boxes
            pass

        # Done
        print_standard('\nDone.')
        pause('Press Enter exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()

# vim: sts=4 sw=4 ts=4
