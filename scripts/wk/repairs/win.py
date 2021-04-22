"""WizardKit: Repairs - Windows"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import platform
import sys

from subprocess import CalledProcessError

from wk.cfg.main  import KIT_NAME_FULL
from wk.exe       import get_procs, run_program, popen_program, wait_for_procs
from wk.kit.tools import run_tool
from wk.log       import format_log_path, update_log_path
from wk.os.win    import (
  reg_delete_value,
  reg_read_value,
  reg_set_value,
  disable_service,
  enable_service,
  stop_service,
  )
from wk.std       import (
  GenericError,
  GenericWarning,
  Menu,
  TryAndPrint,
  ask,
  clear_screen,
  color_string,
  pause,
  print_info,
  print_standard,
  print_warning,
  set_title,
  sleep,
  strip_colors,
  )


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
AUTO_REPAIR_DELAY_IN_SECONDS = 30
AUTO_REPAIR_KEY = fr'Software\{KIT_NAME_FULL}\Auto Repairs'
CONEMU = 'ConEmuPID' in os.environ
OS_VERSION = float(platform.win32_ver()[0])
TRY_PRINT = TryAndPrint()
TRY_PRINT.verbose = True
#for error in ('subprocess.CalledProcessError', 'FileNotFoundError'):
#  TRY_PRINT.add_error(error)


# Auto Repairs
def build_menus(base_menus, title):
  """Build menus, returns dict."""
  menus = {}
  menus['Main'] = Menu(title=f'{title}\n{color_string("Main Menu", "GREEN")}')

  # Main Menu
  for entry in base_menus['Actions']:
    menus['Main'].add_action(entry.name, entry.details)
  for group in base_menus['Options']:
    menus['Main'].add_option(group, {'Selected': True})

  # Options
  menus['Options'] = Menu(title=f'{title}\n{color_string("Options", "GREEN")}')
  for entry in base_menus['Toggles']:
    menus['Options'].add_toggle(entry.name, entry.details)
  menus['Options'].add_action('Main Menu')

  # Run groups
  for group, entries in base_menus['Options'].items():
    menus[group] = Menu(title=f'{title}\n{color_string(group, "GREEN")}')
    menus[group].disabled_str = 'Done'
    for entry in entries:
      menus[group].add_option(entry.name, entry.details)
    menus[group].add_action('Main Menu')

  # Initialize main menu display names
  menus['Main'].update()

  # Done
  return menus


def end_session():
  """End Auto Repairs session."""
  print_info('Ending repair session')
  auto_admin_logon = '0'

  # Delete Auto Repairs session key
  try:
    reg_delete_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')
  except FileNotFoundError:
    LOG.error('Ending repair session but session not started.')

  # Remove logon task
  cmd = [
    'schtasks', '/delete', '/f',
    '/tn', f'{KIT_NAME_FULL}-AutoRepairs',
    ]
  try:
    run_program(cmd)
  except CalledProcessError:
    LOG.error("Failed to remove scheduled task or it doesn't exist.")

  # Disable Autologon
  try:
    auto_admin_logon = reg_read_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'AutoAdminLogon',
      )
  except FileNotFoundError:
    # Ignore and assume it's disabled
    return
  if auto_admin_logon != '0':
    run_tool('Sysinternals', 'Autologon')
    reg_set_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'AutoAdminLogon', '0', 'SZ',
      )
    reg_delete_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'DefaultUserName',
      )
    reg_delete_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'DefaultDomainName',
      )


def get_entry_settings(group, name):
  """Get menu entry settings from the registry, returns dict."""
  key_path = fr'{AUTO_REPAIR_KEY}\{group}\{strip_colors(name)}'
  settings = {}
  for value in ('Done', 'Failed', 'Result'):
    try:
      settings[value] = reg_read_value('HKCU', key_path, value)
    except FileNotFoundError:
      # Ignore and use current settings
      pass

  # Done
  return settings


def init(menus):
  """Initialize Auto Repairs."""
  session_started = is_session_started()

  # Start or resume a repair session
  if session_started:
    load_settings(menus)
    print_info('Resuming session, press CTRL+c to cancel')
    for _x in range(AUTO_REPAIR_DELAY_IN_SECONDS, 0, -1):
      print(f'  {_x} second{"" if _x==1 else "s"} remaining...  \r', end='')
      sleep(1)
    print('')

  # Done
  return session_started


def init_run(options):
  """Initialize Auto Repairs Run."""
  if options.toggles['Kill Explorer']['Selected']:
    atexit.register(start_explorer)
    kill_explorer()
  # TODO: Sync Clock
  # TODO: RKill


def init_session(options):
  """Initialize Auto Repairs session."""
  print_info('Starting repair session')
  reg_set_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted', 1, 'DWORD')

  # Create logon task for Auto Repairs
  cmd = [
    'schtasks', '/create', '/f',
    '/sc', 'ONLOGON',
    '/tn', f'{KIT_NAME_FULL}-AutoRepairs',
    '/rl', 'HIGHEST',
    '/tr', fr'C:\Windows\System32\cmd.exe "/C {sys.executable} {sys.argv[0]}"',
    ]
  run_program(cmd)

  # One-time tasks
  if options.toggles['Use Autologon']['Selected']:
    run_tool('Sysinternals', 'Autologon')
  # TODO: Re-enable reboot()


def is_session_started():
  """Check if session was started, returns bool."""
  session_started = False
  try:
    session_started = reg_read_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')
  except FileNotFoundError:
    pass

  # Done
  return session_started


def load_settings(menus):
  """Load session settings from the registry."""
  for group, menu in menus.items():
    if group == 'Main':
      continue
    for name in menu.options:
      menu.options[name].update(get_entry_settings(group, name))
      if menu.options[name].get('Done', '0') == '1':
        menu.options[name]['Selected'] = False
        menu.options[name]['Disabled'] = True


def run_auto_repairs(base_menus):
  """Run Auto Repairs."""
  update_log_path(dest_name='Auto Repairs', timestamp=True)
  title = f'{KIT_NAME_FULL}: Auto Repairs'
  clear_screen()
  set_title(title)
  print_info(title)
  print('')

  # Generate menus
  print_standard('Initializing...')
  menus = build_menus(base_menus, title)

  # Init
  try:
    session_started = init(menus)
  except KeyboardInterrupt:
    # Assuming session was started and resume countdown was interrupted
    session_started = None

  # Show Menu
  if session_started is None or not session_started:
    while True:
      update_main_menu(menus)
      selection = menus['Main'].simple_select(update=False)
      if selection[0] in base_menus['Options'] or selection[0] == 'Options':
        menus[selection[0]].advanced_select()
      elif 'Start' in selection:
        break
      elif 'Quit' in selection:
        if ask('End session?'):
          end_session()
        raise SystemExit

    # Re-check if a repair session was started
    if session_started is None:
      session_started = is_session_started()

  # Start or resume repairs
  init_run(menus['Options'])
  if not session_started:
    init_session(menus['Options'])

  # Run repairs
  clear_screen()
  for group, menu in menus.items():
    if group in ('Main', 'Options'):
      continue
    for name, details in menu.options.items():
      if details.get('Done', None) == '1':
        continue
      details['Function'](group, name)

  # Done
  end_session()
  print_info('Done')
  pause('Press Enter to exit...')


def save_settings(group, name, done=False, failed=False, result='Unknown'):
  """Load session settings from the registry."""
  key_path = fr'{AUTO_REPAIR_KEY}\{group}\{strip_colors(name)}'
  reg_set_value('HKCU', key_path, 'Done', '1' if done else '0', 'SZ')
  reg_set_value('HKCU', key_path, 'Failed', '1' if failed else '0', 'SZ')
  reg_set_value('HKCU', key_path, 'Result', result, 'SZ')


def update_main_menu(menus):
  """Update main menu based on current selections."""
  index = 1
  skip = 'Reboot'
  for name in menus['Main'].options:
    checkmark = ' '
    selected = [
      _v['Selected'] for _k, _v in menus[name].options.items() if _k != skip
      ]
    if all(selected):
      checkmark = '✓'
    elif any(selected):
      checkmark = '-'
    display_name = f' {index}: [{checkmark}] {name}'
    index += 1
    menus['Main'].options[name]['Display Name'] = display_name


# Auto Repairs: Wrapper Functions
def auto_dism(group, name):
  """Auto DISM repairs, returns bool."""
  needs_reboot = False
  result = TRY_PRINT.run('DISM (RestoreHealth)...', run_dism)

  # Try again if necessary
  if result['Failed']:
    TRY_PRINT.run('Enabling Windows Updates...', enable_windows_updates)
    result = TRY_PRINT.run('DISM (RestoreHealth)...', run_dism)
    TRY_PRINT.run('Disabling Windows Updates...', disable_windows_updates)
    needs_reboot = True

  # Save settings
  save_settings(
    group, name, done=True,
    failed=result['Failed'],
    result=result['Message'],
    )

  # Done
  if needs_reboot:
    reboot()


# OS Built-in Functions
def disable_windows_updates():
  """Disable and stop Windows Updates."""
  stop_service('wuauserv')
  disable_service('wuauserv')


def enable_windows_updates():
  """Enable Windows Updates."""
  enable_service('wuauserv', 'demand')


def kill_explorer():
  """Kill all Explorer processes."""
  cmd = ['taskkill', '/im', 'explorer.exe', '/f']
  run_program(cmd, check=False)


def reboot(timeout=10):
  """Reboot the system."""
  atexit.unregister(start_explorer)
  print_warning(f'Rebooting the system in {timeout} seconds...')
  sleep(timeout)
  cmd = ['shutdown', '-r', '-t', '0']
  run_program(cmd, check=False)
  raise SystemExit


def run_chkdsk_offline():
  """Set filesystem 'dirty bit' to force a CHKDSK during startup."""
  cmd = ['fsutil', 'dirty', 'set', os.environ.get('SYSTEMDRIVE', 'C:')]
  proc = run_program(cmd, check=False)

  # Check result
  if proc.returncode > 0:
    raise GenericError('Failed to set dirty bit.')


def run_chkdsk_online():
  """Run CHKDSK.

  NOTE: If run on Windows 8+ online repairs are attempted.
  """
  cmd = ['CHKDSK', os.environ.get('SYSTEMDRIVE', 'C:')]
  if OS_VERSION >= 8:
    cmd.extend(['/scan', '/perf'])
  if CONEMU:
    cmd.extend(['-new_console:nb', '-new_console:s33V'])
  retried = False

  # Run scan
  run_program(cmd, check=False)
  try:
    proc = get_procs('chkdsk.exe')[0]
    return_code = proc.wait()
  except IndexError:
    # Failed to get CHKDSK process, set return_code to force a retry
    return_code = 255
  if return_code > 1:
    # Try again
    retried = True
    run_program(cmd, check=False)
    try:
      proc = get_procs('chkdsk.exe')[0]
      return_code = proc.wait()
    except IndexError:
      # Failed to get CHKDSK process
      return_code = -1

  # Check result
  if return_code == -1:
    raise GenericError('Failed to find CHKDSK process.')
  if (return_code == 0 and retried) or return_code == 1:
    raise GenericWarning('Repaired (or manually aborted)')
  if return_code > 1:
    raise GenericError('Issue(s) detected')


def run_dism(repair=True):
  """Run DISM to either scan or repair component store health."""
  conemu_args = ['-new_console:nb', '-new_console:s33V'] if CONEMU else []

  # Bail early
  if OS_VERSION < 8:
    raise GenericWarning('Unsupported OS')

  # Run (repair) scan
  log_path = format_log_path(
    log_name=f'DISM_{"Restore" if repair else "Scan"}Health', tool=True,
    )
  log_path.parent.mkdir(parents=True, exist_ok=True)
  cmd = [
    'DISM', '/Online', '/Cleanup-Image',
    '/RestoreHealth' if repair else '/ScanHealth',
    f'/LogPath:{log_path}',
    *conemu_args,
    ]
  run_program(cmd, check=False, pipe=False)
  wait_for_procs('dism.exe')

  # Run check health
  log_path = format_log_path(log_name='DISM_CheckHealth.log', tool=True)
  cmd = [
    'DISM', '/Online', '/Cleanup-Image',
    '/CheckHealth',
    f'/LogPath:{log_path}',
    ]
  proc = run_program(cmd, check=False)

  # Check for errors
  if 'no component store corruption detected' not in proc.stdout.lower():
    raise GenericError('Issue(s) detected')


def run_sfc_scan():
  """Run SFC and save results."""
  cmd = ['sfc', '/scannow']
  log_path = format_log_path(log_name='SFC', tool=True)
  err_path = log_path.with_suffix('.err')

  # Run SFC
  proc = run_program(cmd, check=False, encoding='utf-16le')

  # Save output
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'a') as _f:
    _f.write(proc.stdout)
  with open(err_path, 'a') as _f:
    _f.write(proc.stderr)

  # Check result
  if 'did not find any integrity violations' in proc.stdout:
    pass
  elif 'successfully repaired' in proc.stdout:
    raise GenericWarning('Repaired')
  elif 'found corrupt files' in proc.stdout:
    raise GenericError('Corruption detected')
  else:
    raise OSError


def start_explorer():
  """Start Explorer."""
  popen_program(['explorer.exe'])


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
