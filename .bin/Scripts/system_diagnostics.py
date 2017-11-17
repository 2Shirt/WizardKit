# Wizard Kit: System Diagnostics

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: System Diagnostics Tool')
sys.path.append(os.getcwd())
from functions import *
init_global_vars()
global_vars['LogFile'] = '{LogDir}\\System Diagnostics.log'.format(**global_vars)

def abort():
    print_warning('Aborted.')
    pause("Press Enter to exit...")
    exit_script()

if __name__ == '__main__':
    try:
        stay_awake()
        get_ticket_number()
        os.system('cls')
        other_results = {
            'Error': {
                'CalledProcessError':   'Unknown Error',
            },
            'Warning': {
                'GenericRepair':        'Repaired',
                'UnsupportedOSError':   'Unsupported OS',
            }}
        print_info('Starting System Diagnostics for Ticket #{TicketNumber}\n'.format(**global_vars))
        
        # Sanitize Environment
        print_info('Sanitizing Environment')
        try_and_print(message='Killing processes...',   function=run_process_killer, cs='Done')
        try_and_print(message='Running RKill...',       function=run_rkill, cs='Done')
        try_and_print(message='Running TDSSKiller...',  function=run_tdsskiller, cs='Done')
        
        # Re-run if earlier process was stopped.
        stay_awake()
        
        # Start diags
        print_info('Starting Background Scans')
        check_connection()
        try_and_print(message='Running HitmanPro...',   function=run_hitmanpro, cs='Started')
        try_and_print(message='Running Autoruns...',    function=run_autoruns, cs='Started')
        
        # OS Health Checks
        print_info('OS Health Checks')
        try_and_print(message='CHKDSK ({SYSTEMDRIVE})...'.format(**global_vars['Env']), function=run_chkdsk, other_results=other_results)
        try_and_print(message='SFC scan...',            function=run_sfc_scan, other_results=other_results)
        try_and_print(message='DISM CheckHealth...',    function=run_dism_scan_health, other_results=other_results)
        
        # Export system info
        print_info('Backup System Information')
        try_and_print(message='AIDA64 reports...',      function=run_aida64, cs='Done')
        try_and_print(message='BleachBit report...',    function=run_bleachbit, cs='Done')
        try_and_print(message='Browsers...',            function=backup_browsers, cs='Done')
        try_and_print(message='File listing...',        function=backup_file_list, cs='Done')
        try_and_print(message='Power plans...',         function=backup_power_plans, cs='Done')
        try_and_print(message='Product Keys...',        function=run_produkey, cs='Done')
        try_and_print(message='Registry...',            function=backup_registry, cs='Done')
        
        # Summary
        print_info('Summary')
        try_and_print(message='Temp Size:',             function=show_temp_files_size, silent_function=False)
        show_free_space()
        try_and_print(message='Installed RAM:',         function=show_installed_ram, ns='Unknown', silent_function=False)
        try_and_print(message='Installed Office:',      function=get_installed_office, ns='Unknown', print_return=True)
        try_and_print(message='Product Keys:',          function=get_product_keys, ns='Unknown', print_return=True)
        try_and_print(message='Operating System:',      function=show_os_name, ns='Unknown', silent_function=False)
        try_and_print(message='',                       function=show_os_activation, ns='Unknown', silent_function=False)
        
        # User data
        print_info('User Data')
        show_user_data_summary()
        
        # Upload info
        print_info('Finalizing')
        try_and_print(message='Compressing Info...',    function=compress_info, cs='Done')
        try_and_print(message='Uploading to NAS...',    function=upload_info, cs='Done')
        
        # Done
        print_standard('\nDone.')
        pause('Press Enter to exit...')
        exit_script()
    except SystemExit:
        pass
    except:
        major_exception()
