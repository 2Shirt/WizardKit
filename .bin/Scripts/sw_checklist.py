# Wizard Kit: Software Checklist

import os

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Software Checklist Tool')
from functions import *
init_global_vars()
set_global_vars(LogFile='{LogDir}\\Software Checklist.log'.format(**global_vars))

def abort():
    print_warning('Aborted.')
    exit_script()

if __name__ == '__main__':
    stay_awake()
    get_ticket_number()
    os.system('cls')
    print_info('Starting Software Checklist for Ticket #{TicketNumber}\n'.format(**global_vars))
    
    # Configure
    print_info('Configure')
    try_and_print(message='Updating Clock...',      function=update_clock, cs='Done')
    if global_vars['OS']['Version'] in ['8', '10']:
        try_and_print(message='Classic Start...',   function=config_classicstart, cs='Done')
        try_and_print(message='Explorer...',        function=config_explorer, cs='Done')
    
    # Cleanup
    print_info('Cleanup')
    try_and_print(message='Desktop...',            function=cleanup_desktop, cs='Done')
    try_and_print(message='AdwCleaner...',         function=cleanup_adwcleaner, cs='Done')
    try_and_print(message='ESET...',               function=uninstall_eset, cs='Done')
    # try_and_print(message='MBAM...',             function=uninstall_mbam, cs='Done')
    try_and_print(message='Super Anti-Spyware...', function=uninstall_sas, cs='Done')
    
    # Export system info
    print_info('Backup System Information')
    try_and_print(message='AIDA64 reports...',     function=run_aida64, cs='Done')
    # try_and_print(message='Browsers...',         function=backup_browsers, cs='Done')
    try_and_print(message='File listing...',       function=backup_file_list, cs='Done')
    try_and_print(message='Power plans...',        function=backup_power_plans, cs='Done')
    try_and_print(message='Product Keys...',       function=run_produkey, cs='Done')
    try_and_print(message='Registry...',           function=backup_registry, cs='Done')
    
    # User data
    print_info('User Data')
    show_user_data_summary()
    
    # Summary
    print_info('Summary')
    try_and_print(message='Operating System:',      function=show_os_name, ns='Unknown', silent_function=False)
    try_and_print(message='',                       function=show_os_activation, ns='Unknown', silent_function=False)
    try_and_print(message='Installed Office:',      function=get_installed_office, ns='Unknown', print_return=True)
    show_free_space()
    try_and_print(message='Installed RAM:',         function=show_installed_ram, ns='Unknown', silent_function=False)
    
    # Upload info
    print_info('Finalizing')
    try_and_print(message='Compressing Info...',   function=compress_info, cs='Done')
    try_and_print(message='Uploading to NAS...',   function=upload_info, cs='Done')
    
    # Play audio, show devices, open Windows updates, and open Activation if necessary
    popen_program('devmgmt.msc')
    run_hwinfo_sensors()
    if global_vars['OS']['Version'] == '10':
        popen_program(['control', '/name', 'Microsoft.WindowsUpdate'])
    else:
        popen_program('wuapp')
    if 'The machine is permanently activated.' not in global_vars['OS']['Activation']:
        popen_program('slui')
    sleep(3)
    run_xmplay()
    
    # Done
    print_standard('\nDone.')
    pause('Press Enter exit...')
    exit_script()
