# Wizard Kit: System Diagnostics

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.browsers import *
from functions.info import *
from functions.product_keys import *
from functions.repairs import *
from functions.sw_diags import *
init_global_vars()
os.system('title {}: System Diagnostics Tool'.format(KIT_NAME_FULL))
set_log_file('System Diagnostics.log')

# Static Variables
BLEACH_BIT_CLEANERS = {
  'Applications': (
    'adobe_reader.cache',
    'adobe_reader.tmp',
    'amule.tmp',
    'flash.cache',
    'gimp.tmp',
    'hippo_opensim_viewer.cache',
    'java.cache',
    'libreoffice.cache',
    'liferea.cache',
    'miro.cache',
    'openofficeorg.cache',
    'pidgin.cache',
    'secondlife_viewer.Cache',
    'thunderbird.cache',
    'vuze.backup_files',
    'vuze.cache',
    'vuze.tmp',
    'yahoo_messenger.cache',
  ),
  'Browsers': (
    'chromium.cache',
    'chromium.current_session',
    'firefox.cache',
    'firefox.session_restore',
    'google_chrome.cache',
    'google_chrome.session',
    'google_earth.temporary_files',
    'internet_explorer.temporary_files',
    'opera.cache',
    'opera.current_session',
    'safari.cache',
    'seamonkey.cache',
  ),
  'System': (
    'system.clipboard',
    'system.tmp',
    'winapp2_windows.jump_lists',
    'winapp2_windows.ms_search',
    'windows_explorer.run',
    'windows_explorer.search_history',
    'windows_explorer.thumbnails',
  ),
}

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    print_info('{}: System Diagnostics Tool\n'.format(KIT_NAME_FULL))
    ticket_number = get_ticket_number()
    other_results = {
      'Error': {
        'CalledProcessError':   'Unknown Error',
        'FileNotFoundError':  'File not found',
      },
      'Warning': {
        'GenericRepair':    'Repaired',
        'UnsupportedOSError':   'Unsupported OS',
      }}
    if ENABLED_TICKET_NUMBERS:
      print_info('Starting System Diagnostics for Ticket #{}\n'.format(
        ticket_number))

    # Sanitize Environment
    print_info('Sanitizing Environment')
    try_and_print(message='Running RKill...',
      function=run_rkill, cs='Done', other_results=other_results)
    try_and_print(message='Running TDSSKiller...',
      function=run_tdsskiller, cs='Done', other_results=other_results)

    # Re-run if earlier process was stopped.
    stay_awake()

    # Start diags
    print_info('Starting Background Scans')
    check_connection()
    try_and_print(message='Running HitmanPro...',
      function=run_hitmanpro, cs='Started', other_results=other_results)
    try_and_print(message='Running Autoruns...',
      function=run_autoruns, cs='Started', other_results=other_results)

    # OS Health Checks
    print_info('OS Health Checks')
    try_and_print(
      message='CHKDSK ({SYSTEMDRIVE})...'.format(**global_vars['Env']),
      function=run_chkdsk, other_results=other_results)
    try_and_print(message='SFC scan...',
      function=run_sfc_scan, other_results=other_results)
    try_and_print(message='DISM CheckHealth...',
      function=run_dism, other_results=other_results, repair=False)

    # Scan for supported browsers
    print_info('Scanning for browsers')
    scan_for_browsers()

    # Run BleachBit cleaners
    print_info('BleachBit Cleanup')
    for k, v in sorted(BLEACH_BIT_CLEANERS.items()):
      try_and_print(message='  {}...'.format(k),
        function=run_bleachbit,
        cs='Done', other_results=other_results,
        cleaners=v, preview=True)

    # Export system info
    print_info('Backup System Information')
    try_and_print(message='AIDA64 reports...',
      function=run_aida64, cs='Done', other_results=other_results)
    backup_browsers()
    try_and_print(message='File listing...',
      function=backup_file_list, cs='Done', other_results=other_results)
    try_and_print(message='Power plans...',
      function=backup_power_plans, cs='Done')
    try_and_print(message='Product Keys...',
      function=run_produkey, cs='Done', other_results=other_results)
    try_and_print(message='Registry...',
      function=backup_registry, cs='Done', other_results=other_results)

    # Summary
    print_info('Summary')
    try_and_print(message='Operating System:',
      function=show_os_name, ns='Unknown', silent_function=False)
    try_and_print(message='Activation:',
      function=show_os_activation, ns='Unknown', silent_function=False)
    try_and_print(message='Installed RAM:',
      function=show_installed_ram, ns='Unknown', silent_function=False)
    show_free_space()
    try_and_print(message='Temp Size:',
      function=show_temp_files_size, silent_function=False)
    try_and_print(message='Installed Antivirus:',
      function=get_installed_antivirus, ns='Unknown',
      other_results=other_results, print_return=True)
    try_and_print(message='Installed Office:',
      function=get_installed_office, ns='Unknown',
      other_results=other_results, print_return=True)
    try_and_print(message='Product Keys:',
      function=get_product_keys, ns='Unknown', print_return=True)

    # User data
    print_info('User Data')
    try:
      show_user_data_summary()
    except Exception:
      print_error('  Unknown error.')

    # Done
    print_standard('\nDone.')
    pause('Press Enter to exit...')
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
