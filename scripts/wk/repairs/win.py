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
  show_data,
  sleep,
  strip_colors,
  )


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
AUTO_REPAIR_DELAY_IN_SECONDS = 30
AUTO_REPAIR_KEY = fr'Software\{KIT_NAME_FULL}\Auto Repairs'
CONEMU = 'ConEmuPID' in os.environ
OS_VERSION = float(platform.win32_ver()[0])
WIDTH = 50
TRY_PRINT = TryAndPrint()
TRY_PRINT.width = WIDTH
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
  for group in base_menus['Groups']:
    menus['Main'].add_option(group, {'Selected': True})

  # Options
  menus['Options'] = Menu(title=f'{title}\n{color_string("Options", "GREEN")}')
  for entry in base_menus['Options']:
    menus['Options'].add_option(entry.name, entry.details)
  menus['Options'].add_action('All')
  menus['Options'].add_action('None')
  menus['Options'].add_action('Main Menu', {'Separator': True})
  menus['Options'].add_action('Quit')

  # Run groups
  for group, entries in base_menus['Groups'].items():
    menus[group] = Menu(title=f'{title}\n{color_string(group, "GREEN")}')
    menus[group].disabled_str = 'Locked'
    for entry in entries:
      menus[group].add_option(entry.name, entry.details)
    menus[group].add_action('All')
    menus[group].add_action('None')
    menus[group].add_action('Select Skipped Entries', {'Separator': True})
    menus[group].add_action('Unlock All Entries')
    menus[group].add_action('Main Menu', {'Separator': True})
    menus[group].add_action('Quit')

  # Initialize main menu display names
  menus['Main'].update()

  # Done
  return menus


def end_session():
  """End Auto Repairs session."""
  print_info('Ending repair session')
  auto_admin_logon = '0'

  # Delete Auto Repairs keys
  try:
    reg_delete_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')
  except FileNotFoundError:
    LOG.error('Ending repair session but session not started.')
  try:
    cmd = ['reg', 'delete', fr'HKCU\{AUTO_REPAIR_KEY}', '/f']
    run_program(cmd)
  except CalledProcessError:
    LOG.error('Failed to remote Auto Repairs session settings')

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
  for value in ('done', 'failed', 'message', 'selected', 'skipped', 'warning'):
    try:
      settings[value.title()] = reg_read_value('HKCU', key_path, value)
    except FileNotFoundError:
      # Ignore and use current settings
      pass

  # Disable previously run or skipped entries
  if settings.get('Done', False) or settings.get('Skipped', False):
    settings['Disabled'] = True

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
  if options['Kill Explorer']['Selected']:
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
  if options['Use Autologon']['Selected']:
    run_tool('Sysinternals', 'Autologon')
  # TODO: TDSSKiller?
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
    try:
      show_main_menu(base_menus, menus)
    except SystemExit:
      if ask('End session?'):
        end_session()
      raise

    # Re-check if a repair session was started
    if session_started is None:
      session_started = is_session_started()

  # Start or resume repairs
  save_selection_settings(menus)
  init_run(menus['Options'].options)
  if not session_started:
    init_session(menus['Options'].options)

  # Run repairs
  clear_screen()
  for group, menu in menus.items():
    if group in ('Main', 'Options'):
      continue
    run_group(group, menu)

  # Done
  end_session()
  print_info('Done')
  pause('Press Enter to exit...')


def run_group(group, menu):
  """Run entries in group if appropriate."""
  print_info(f'  {group}')
  for name, details in menu.options.items():
    name_str = strip_colors(name)
    skipped = details.get('Skipped', False)
    done = details.get('Done', False)
    disabled = details.get('Disabled', False)
    selected = details.get('Selected', False)

    # Selection changed
    if (skipped or done) and not disabled and selected:
      save_settings(group, name, done=False, skipped=False)
      details['Function'](group, name)
      continue

    # Previously skipped
    if skipped:
      show_data(f'{name_str}...', 'Skipped', 'YELLOW', width=WIDTH)
      continue

    # Previously ran
    if done:
      color = 'GREEN'
      if details.get('Warning', False):
        color = 'YELLOW'
      elif details.get('Failed', False):
        color = 'RED'
      show_data(
        f'{name_str}...',
        details.get('Message', 'Unknown'), color, width=WIDTH,
        )
      continue

    # Not selected
    if not selected:
      show_data(f'{name_str}...', 'Skipped', 'YELLOW', width=WIDTH)
      save_settings(group, name, skipped=True)
      continue

    # Selected
    details['Function'](group, name)


def save_selection_settings(menus):
  """Save selections in the registry."""
  for group, menu in menus.items():
    if group == 'Main':
      continue
    for name, details in menu.options.items():
      save_settings(
        group, name,
        disabled=details.get('Disabled', False),
        selected=details.get('Selected', False),
        )


def save_settings(group, name, result=None, **kwargs):
  """Save entry settings in the registry."""
  key_path = fr'{AUTO_REPAIR_KEY}\{group}\{strip_colors(name)}'

  # Get values from TryAndPrint result
  if result:
    kwargs.update({
      'done': True,
      'failed': result['Failed'],
      'message': result['Message'],
      })

  # Write values to registry
  for value_name, data in kwargs.items():
    if isinstance(data, bool):
      data = 1 if data else 0
    if isinstance(data, int):
      data_type = 'DWORD'
    elif isinstance(data, str):
      data_type = 'SZ'
    else:
      raise TypeError(f'Invalid data: "{data}" ({type(data)})')
    reg_set_value('HKCU', key_path, value_name, data, data_type)


def show_main_menu(base_menus, menus):
  """Show main menu and handle actions."""
  while True:
    update_main_menu(menus)
    selection = menus['Main'].simple_select(update=False)
    if selection[0] in base_menus['Groups'] or selection[0] == 'Options':
      show_sub_menu(menus[selection[0]])
    elif 'Start' in selection:
      break
    elif 'Quit' in selection:
      raise SystemExit


def show_sub_menu(menu):
  """Show sub-menu and handle sub-menu actions."""
  while True:
    selection = menu.advanced_select()
    if 'Main Menu' in selection:
      break
    if 'Quit' in selection:
      raise SystemExit

    # Modify entries
    key = 'Selected'
    unlock_all = False
    unlock_skipped = False
    if 'Select Skipped Entries' in selection:
      key = 'Disabled'
      unlock_skipped = True
      value = False
    if 'Unlock All Entries' in selection:
      key = 'Disabled'
      unlock_all = True
      value = False
    else:
      value = 'All' in selection
    for name in menu.options:
      if (unlock_all
          or (unlock_skipped and not menu.options[name].get('Selected', False))
          or not menu.options[name].get('Disabled', False)
          ):
        menu.options[name][key] = value


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
    warning=not result['Failed'] and needs_reboot,
    message=result['Message'],
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
