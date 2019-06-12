# Wizard Kit: Check or repair the %SYSTEMDRIVE% filesystem via CHKDSK

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from functions.repairs import *
init_global_vars()
os.system('title {}: Check Disk Tool'.format(KIT_NAME_FULL))
set_log_file('Check Disk.log')

if __name__ == '__main__':
  try:
    stay_awake()
    clear_screen()
    other_results = {
      'Error': {
        'CalledProcessError':   'Unknown Error',
      },
      'Warning': {
        'GenericRepair':    'Repaired',
        'UnsupportedOSError':   'Unsupported OS',
      }}
    options = [
      {'Name': 'Run CHKDSK scan (read-only)', 'Repair': False},
      {'Name': 'Schedule CHKDSK scan (offline repair)', 'Repair': True}]
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    selection = menu_select(
      '{}: Check Disk Menu\n'.format(KIT_NAME_FULL),
      main_entries=options,
      action_entries=actions)
    print_info('{}: Check Disk Menu\n'.format(KIT_NAME_FULL))
    if selection == 'Q':
      abort()
    elif selection.isnumeric():
      repair = options[int(selection)-1]['Repair']
      if repair:
        cs = 'Scheduled'
      else:
        cs = 'No issues'
      message = 'CHKDSK ({SYSTEMDRIVE})...'.format(**global_vars['Env'])
      try_and_print(message=message, function=run_chkdsk,
        cs=cs, other_results=other_results, repair=repair)
    else:
      abort()

    # Done
    print_success('Done.')
    pause("Press Enter to exit...")
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except:
    major_exception()

# vim: sts=2 sw=2 ts=2
