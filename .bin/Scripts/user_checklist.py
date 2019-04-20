# Wizard Kit: User Checklist

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.browsers import *
from functions.cleanup import *
from functions.setup import *
init_global_vars()
os.system('title {}: User Checklist Tool'.format(KIT_NAME_FULL))
set_log_file('User Checklist ({USERNAME}).log'.format(**global_vars['Env']))

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    print_info('{}: User Checklist\n'.format(KIT_NAME_FULL))
    other_results = {
      'Warning': {
        'NotInstalledError': 'Not installed',
        'NoProfilesError': 'No profiles found',
      }}
    answer_config_browsers = ask('Install adblock?')
    if answer_config_browsers:
      answer_reset_browsers = ask(
        'Reset browsers to safe defaults first?')
    if global_vars['OS']['Version'] == '10':
      answer_config_classicshell = ask('Configure ClassicShell?')
      answer_config_explorer_user = ask('Configure Explorer?')

    # Cleanup
    print_info('Cleanup')
    try_and_print(message='Desktop...',
      function=cleanup_desktop, cs='Done')

    # Scan for supported browsers
    print_info('Scanning for browsers')
    scan_for_browsers()

    # Homepages
    print_info('Current homepages')
    list_homepages()

    # Backup
    print_info('Backing up browsers')
    backup_browsers()

    # Reset
    if answer_config_browsers and answer_reset_browsers:
      print_info('Resetting browsers')
      reset_browsers()

    # Configure
    print_info('Configuring programs')
    if answer_config_browsers:
      install_adblock()
    if global_vars['OS']['Version'] == '10':
      if answer_config_classicshell:
        try_and_print(message='ClassicStart...',
          function=config_classicstart, cs='Done')
      if answer_config_explorer_user:
        try_and_print(message='Explorer...',
          function=config_explorer_user, cs='Done')
      if (not answer_config_browsers
        and not answer_config_classicshell
        and not answer_config_explorer_user):
        print_warning('    Skipped')
    else:
      if not answer_config_browsers:
        print_warning('    Skipped')

    # Restart Explorer
    try_and_print(message='Restarting Explorer...',
      function=restart_explorer, cs='Done')

    # Run speedtest
    popen_program(['start', '', 'https://fast.com'], shell=True)

    # Done
    print_standard('\nDone.')
    pause('Press Enter to exit...')
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
