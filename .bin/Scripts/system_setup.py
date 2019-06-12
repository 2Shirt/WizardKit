'''Wizard Kit: System Setup'''
# pylint: disable=wildcard-import,wrong-import-position
# vim: sts=2 sw=2 ts=2

import os
import sys

# Init
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from collections import OrderedDict
from functions.activation import *
from functions.browsers import *
from functions.cleanup import *
from functions.info import *
from functions.product_keys import *
from functions.setup import *
from functions.sw_diags import *
from functions.windows_updates import *
init_global_vars()
os.system('title {}: System Setup'.format(KIT_NAME_FULL))
set_log_file('System Setup.log')


# STATIC VARIABLES
# pylint: disable=bad-whitespace,line-too-long
OTHER_RESULTS = {
  'Error': {
    'BIOSKeyNotFoundError':     'BIOS KEY NOT FOUND',
    'CalledProcessError':       'UNKNOWN ERROR',
    'FileNotFoundError':        'FILE NOT FOUND',
    'GenericError':             'UNKNOWN ERROR',
    'Not4KAlignedError':        'FALSE',
    'SecureBootDisabledError':  'DISABLED',
    'WindowsUnsupportedError':  'UNSUPPORTED',
  },
  'Warning': {
    'GenericRepair':            'REPAIRED',
    'NoProfilesError':          'NO PROFILES FOUND',
    'NotInstalledError':        'NOT INSTALLED',
    'OSInstalledLegacyError':   'OS INSTALLED LEGACY',
    'SecureBootNotAvailError':  'NOT AVAILABLE',
    'SecureBootUnknownError':   'UNKNOWN',
    'UnsupportedOSError':       'UNSUPPORTED OS',
    'WindowsOutdatedError':     'OUTDATED',
    },
  }
SETUP_ACTIONS = OrderedDict({
  # Install software
  'Installing Programs':    {'Info': True},
  'VCR':                    {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_vcredists, 'Just run': True,},
  'LibreOffice':            {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_libreoffice,
                             'If answer': 'LibreOffice', 'KWArgs': {'quickstart': False, 'register_mso_types': True, 'use_mso_formats': False, 'vcredist': False},
                             },
  'Ninite bundle':          {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_ninite_bundle, 'KWArgs': {'cs': 'STARTED'},},

  # Browsers
  'Scanning for browsers':  {'Info': True},
  'Scan':                   {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': scan_for_browsers, 'Just run': True, 'KWArgs': {'skip_ie': True},},
  'Backing up browsers':    {'Info': True},
  'Backup browsers':        {'New': False,  'Dat': True,  'Cur': True,  'HW': False, 'Function': backup_browsers, 'Just run': True,},

  # Install extensions
  'Installing Extensions':  {'Info': True},
  'Classic Shell skin':     {'New': True,   'Dat': True,  'Cur': False, 'HW': False, 'Function': install_classicstart_skin, 'Win10 only': True,},
  'Chrome extensions':      {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_chrome_extensions,},
  'Firefox extensions':     {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_firefox_extensions,},

  # Configure software'
  'Configuring Programs':   {'Info': True},
  'Browser add-ons':        {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': install_adblock, 'Just run': True,
                             'Pause': 'Please enable uBlock Origin for all browsers',
                             },
  'Classic Start':          {'New': True,   'Dat': True,  'Cur': False, 'HW': False, 'Function': config_classicstart, 'Win10 only': True,},
  'Config Windows Updates': {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': config_windows_updates, 'Win10 only': True,},
  'Enable Windows Updates': {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': enable_windows_updates, 'KWArgs': {'silent': True},},
  'Explorer (system)':      {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': config_explorer_system, 'Win10 only': True,},
  'Explorer (user)':        {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': config_explorer_user, 'Win10 only': True,},
  'Restart Explorer':       {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': restart_explorer,},
  'Restore default UAC':    {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': restore_default_uac,},
  'Update Clock':           {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': update_clock,},

  # Cleanup
  'Cleaning up':            {'Info': True},
  'AdwCleaner':             {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': cleanup_adwcleaner,},
  'Desktop':                {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': cleanup_desktop,},
  'KIT_NAME_FULL':          {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': delete_empty_folders,},

  # System Info
  'Exporting system info':  {'Info': True},
  'AIDA64 Report':          {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': run_aida64,},
  'File listing':           {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': backup_file_list,},
  'Power plans':            {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': backup_power_plans,},
  'Product Keys':           {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': run_produkey,},
  'Registry':               {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': backup_registry,},

  # Show Summary
  'Summary':                {'Info': True},
  'Operating System':       {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': show_os_name, 'KWArgs': {'ns': 'UNKNOWN', 'silent_function': False},},
  'Activation':             {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': show_os_activation, 'KWArgs': {'ns': 'UNKNOWN', 'silent_function': False},},
  'BIOS Activation':        {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': activate_with_bios, 'If not activated': True,},
  'Secure Boot':            {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': check_secure_boot_status, 'KWArgs': {'show_alert': False},},
  'Installed RAM':          {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': show_installed_ram, 'KWArgs': {'ns': 'UNKNOWN', 'silent_function': False},},
  'Temp size':              {'New': False,  'Dat': False, 'Cur': True,  'HW': False, 'Function': show_temp_files_size, 'KWArgs': {'ns': 'UNKNOWN', 'silent_function': False},},
  'Show free space':        {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': show_free_space, 'Just run': True,},
  'Installed AV':           {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': get_installed_antivirus, 'KWArgs': {'ns': 'UNKNOWN', 'print_return': True},},
  'Installed Office':       {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': get_installed_office, 'KWArgs': {'ns': 'UNKNOWN', 'print_return': True},},
  'Partitions 4K aligned':  {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': check_4k_alignment, 'KWArgs': {'cs': 'TRUE', 'ns': 'FALSE'},},

  # Open things
  'Opening Programs':       {'Info': True},
  'Device Manager':         {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': open_device_manager, 'KWArgs': {'cs': 'STARTED'},},
  'HWiNFO sensors':         {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': run_hwinfo_sensors, 'KWArgs': {'cs': 'STARTED'},},
  'Speed test':             {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': open_speedtest, 'KWArgs': {'cs': 'STARTED'},},
  'Windows Updates':        {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': open_windows_updates, 'KWArgs': {'cs': 'STARTED'},},
  'Windows Activation':     {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Function': open_windows_activation, 'If not activated': True, 'KWArgs': {'cs': 'STARTED'},},
  'Sleep':                  {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': sleep, 'Just run': True, 'KWArgs': {'seconds': 3},},
  'XMPlay':                 {'New': True,   'Dat': True,  'Cur': True,  'HW': True,  'Function': run_xmplay, 'KWArgs': {'cs': 'STARTED'},},
  })
SETUP_ACTION_KEYS = (
  'Function',
  'If not activated',
  'Info',
  'Just run',
  'KWArgs',
  'Pause',
  )
SETUP_QUESTIONS = {
  # AV
  'MSE':          {'New': None,   'Dat': None,  'Cur': None,  'HW': False, 'Ninite': True},

  # LibreOffice
  'LibreOffice':  {'New': None,   'Dat': None,  'Cur': None,  'HW': False, 'Ninite': True},

  # Ninite
  'Base':         {'New': True,   'Dat': True,  'Cur': True,  'HW': False, 'Ninite': True},
  'Missing':      {'New': False,  'Dat': True,  'Cur': False, 'HW': False, 'Ninite': True},
  'Standard':     {'New': True,   'Dat': True,  'Cur': False, 'HW': False, 'Ninite': True},
  }
# pylint: enable=bad-whitespace,line-too-long


# Functions
def check_os_and_abort():
  """Check OS and prompt to abort if not supported."""
  result = try_and_print(
    message='OS support status...',
    function=check_os_support_status,
    cs='GOOD',
    )
  if not result['CS'] and 'Unsupported' in result['Error']:
    print_warning('OS version not supported by this script')
    if not ask('Continue anyway? (NOT RECOMMENDED)'):
      abort()


def get_actions(setup_mode, answers):
  """Get actions to perform based on setup_mode, returns OrderedDict."""
  actions = OrderedDict({})
  for _key, _val in SETUP_ACTIONS.items():
    _action = {}
    _if_answer = _val.get('If answer', False)
    _win10_only = _val.get('Win10 only', False)

    # Set enabled status
    _enabled = _val.get(setup_mode, False)
    if _if_answer:
      _enabled = _enabled and answers[_if_answer]
    if _win10_only:
      _enabled = _enabled and global_vars['OS']['Version'] == '10'
    _action['Enabled'] = _enabled

    # Set other keys
    for _sub_key in SETUP_ACTION_KEYS:
      _action[_sub_key] = _val.get(_sub_key, None)

    # Fix KWArgs
    if _action.get('KWArgs', {}) is None:
      _action['KWArgs'] = {}

    # Handle "special" actions
    if _key == 'KIT_NAME_FULL':
      # Cleanup WK folders
      _key = KIT_NAME_FULL
      _action['KWArgs'] = {'folder_path': global_vars['ClientDir']}
    elif _key == 'Ninite bundle':
      # Add install_ninite_bundle() kwargs
      _action['KWArgs'].update({
        kw.lower(): kv for kw, kv in answers.items()
        if SETUP_QUESTIONS.get(kw, {}).get('Ninite', False)
        })
    elif _key == 'Explorer (user)':
      # Explorer settings (user)
      _action['KWArgs'] = {'setup_mode': setup_mode}

    # Add to dict
    actions[_key] = _action

  return actions


def get_answers(setup_mode):
  """Get setup answers based on setup_mode and user input, returns dict."""
  answers = {k: v.get(setup_mode, False) for k, v in SETUP_QUESTIONS.items()}

  # Answer setup questions as needed
  if answers['MSE'] is None and global_vars['OS']['Version'] == '7':
    answers.update(get_av_selection())

  if answers['LibreOffice'] is None:
    answers['LibreOffice'] = ask('Install LibreOffice?')

  return answers


def get_av_selection():
  """Get AV selection."""
  av_answers = {
    'MSE': False,
    }
  av_options = [
    {
      'Name': 'Microsoft Security Essentials',
      'Disabled': global_vars['OS']['Version'] not in ['7'],
      },
    ]
  actions = [
    {'Name': 'None', 'Letter': 'N'},
    {'Name': 'Quit', 'Letter': 'Q'},
    ]

  # Show menu
  selection = menu_select(
    'Please select an option to install',
    main_entries=av_options,
    action_entries=actions)
  if selection.isnumeric():
    index = int(selection) - 1
    if 'Microsoft' in av_options[index]['Name']:
      av_answers['MSE'] = True
  elif selection == 'Q':
    abort()

  return av_answers


def get_mode():
  """Get mode via menu_select, returns str."""
  setup_mode = None
  mode_options = [
    {'Name': 'New', 'Display Name': 'New / Clean install (no data)'},
    {'Name': 'Dat', 'Display Name': 'Clean install with data migration'},
    {'Name': 'Cur', 'Display Name': 'Original OS (post-repair or overinstall)'},
    {'Name': 'HW', 'Display Name': 'Hardware service (i.e. no software work)'},
    ]
  actions = [
    {'Name': 'Quit', 'Letter': 'Q'},
    ]

  # Get selection
  selection = menu_select(
    'Please select a setup mode',
    main_entries=mode_options,
    action_entries=actions)
  if selection.isnumeric():
    index = int(selection) - 1
    setup_mode = mode_options[index]['Name']
  elif selection == 'Q':
    abort()

  return setup_mode


def main():
  """Main function."""
  stay_awake()
  clear_screen()

  # Check installed OS
  check_os_and_abort()

  # Get setup mode
  setup_mode = get_mode()

  # Get answers to setup questions
  answers = get_answers(setup_mode)

  # Get actions to perform
  actions = get_actions(setup_mode, answers)

  # Perform actions
  for action, values in actions.items():
    kwargs = values.get('KWArgs', {})

    # Print info lines
    if values.get('Info', False):
      print_info(action)
      continue

    # Print disabled actions
    if not values.get('Enabled', False):
      show_data(
        message='{}...'.format(action),
        data='DISABLED',
        warning=True,
        )
      continue

    # Check Windows activation if requested
    if values.get('If not activated', False) and windows_is_activated():
      # Skip
      continue

    # Run function
    if values.get('Just run', False):
      values['Function'](**kwargs)
    else:
      result = try_and_print(
        message='{}...'.format(action),
        function=values['Function'],
        other_results=OTHER_RESULTS,
        **kwargs)

    # Wait for Ninite proc(s)
    if action == 'Ninite bundle':
      print_standard('Waiting for installations to finish...')
      try:
        for proc in result['Out']:
          proc.wait()
      except KeyboardInterrupt:
        pass

    # Pause
    if values.get('Pause', False):
      print_standard(values['Pause'])
      pause()

  # Show alert box for SecureBoot issues
  try:
    check_secure_boot_status(show_alert=True)
  except Exception: # pylint: disable=broad-except
    # Ignoring exceptions since we just want to show the popup
    pass

  # Done
  pause('Press Enter to exit... ')


if __name__ == '__main__':
  try:
    main()
    exit_script()
  except SystemExit as sys_exit:
    exit_script(sys_exit.code)
  except: # pylint: disable=bare-except
    major_exception()
