# Wizard Kit: New system setup

import os
import sys

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.getcwd())
from functions.activation import *
from functions.browsers import *
from functions.cleanup import *
from functions.info import *
from functions.product_keys import *
from functions.setup import *
from functions.sw_diags import *
init_global_vars()
os.system('title {}: New System Setup'.format(KIT_NAME_FULL))
set_log_file('New System Setup.log')

if __name__ == '__main__':
  other_results = {
    'Error': {
      'BIOSKeyNotFoundError':     'BIOS key not found',
      'CalledProcessError':       'Unknown Error',
      'FileNotFoundError':        'File not found',
      'GenericError':             'Unknown Error',
      'SecureBootDisabledError':  'Disabled',
    },
    'Warning': {
      'GenericRepair':            'Repaired',
      'NoProfilesError':          'No profiles found',
      'NotInstalledError':        'Not installed',
      'OSInstalledLegacyError':   'OS installed Legacy',
      'SecureBootNotAvailError':  'Not available',
      'SecureBootUnknownError':   'Unknown',
      'UnsupportedOSError':       'Unsupported OS',
    }}
  try:
    stay_awake()
    clear_screen()

    # Check installed OS
    if os_is_unsupported(show_alert=False):
      print_warning('OS version not supported by this script')
      if not ask('Continue anyway? (NOT RECOMMENDED)'):
        abort()

    # Install Adobe Reader?
    answer_adobe_reader = ask('Install Adobe Reader?')

    # Install LibreOffice?
    answer_libreoffice = ask('Install LibreOffice?')

    # Install MSE?
    if global_vars['OS']['Version'] == '7':
      answer_mse = ask('Install MSE?')
    else:
      answer_mse = False

    # Install software
    print_info('Installing Programs')
    install_vcredists()
    if answer_adobe_reader:
      try_and_print(message='Adobe Reader DC...',
        function=install_adobe_reader, other_results=other_results)
    result = try_and_print(
      message='Ninite bundle...',
      function=install_ninite_bundle, cs='Started',
      mse=answer_mse, libreoffice=answer_libreoffice,
      other_results=other_results)
    for proc in result['Out']:
      # Wait for all processes to finish
      proc.wait()

    # Scan for supported browsers
    print_info('Scanning for browsers')
    scan_for_browsers()

    # Install extensions
    print_info('Installing Extensions')
    try_and_print(message='Classic Shell skin...',
      function=install_classicstart_skin,
      other_results=other_results)
    try_and_print(message='Google Chrome extensions...',
      function=install_chrome_extensions)
    try_and_print(message='Mozilla Firefox extensions...',
      function=install_firefox_extensions,
      other_results=other_results)

    # Configure software
    print_info('Configuring programs')
    install_adblock()
    if global_vars['OS']['Version'] == '10':
      try_and_print(message='ClassicStart...',
        function=config_classicstart, cs='Done')
      try_and_print(message='Explorer...',
        function=config_explorer_user, cs='Done')

    # Configure system
    print_info('Configuring system')
    if global_vars['OS']['Version'] == '10':
      try_and_print(message='Explorer...',
        function=config_explorer_system, cs='Done')
      try_and_print(message='Disabling telemetry...',
        function=disable_windows_telemetry, cs='Done')
      try_and_print(message='Windows Updates...',
        function=config_windows_updates, cs='Done')
    try_and_print(message='Updating Clock...',
      function=update_clock, cs='Done')

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
    pause('Press Enter to exit...')
    exit_script()
  except SystemExit:
    pass
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
