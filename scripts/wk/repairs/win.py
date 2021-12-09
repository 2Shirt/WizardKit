"""WizardKit: Repairs - Windows"""
# pylint: disable=too-many-lines
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import re
import sys
import time

from subprocess       import CalledProcessError, DEVNULL

from wk.cfg.main      import KIT_NAME_FULL, KIT_NAME_SHORT, WINDOWS_TIME_ZONE
from wk.cfg.repairs   import (
  AUTO_REPAIR_DELAY_IN_SECONDS,
  AUTO_REPAIR_KEY,
  BLEACH_BIT_CLEANERS,
  CUSTOM_POWER_PLAN_DESC,
  CUSTOM_POWER_PLAN_NAME,
  POWER_PLANS,
  POWER_PLAN_SLEEP_TIMEOUTS,
  REG_UAC_DEFAULTS_WIN7,
  REG_UAC_DEFAULTS_WIN10,
  WIDTH,
  )
from wk.exe           import (
  get_procs,
  run_program,
  popen_program,
  wait_for_procs,
  )
from wk.io            import (
  copy_file,
  delete_folder,
  get_path_obj,
  non_clobber_path,
  rename_item,
  )
from wk.kit.tools     import (download_tool, get_tool_path, run_tool)
from wk.log           import format_log_path, update_log_path
from wk.os.win        import (
  OS_VERSION,
  get_timezone,
  set_timezone,
  reg_delete_value,
  reg_read_value,
  reg_set_value,
  reg_write_settings,
  disable_service,
  enable_service,
  stop_service,
  )
from wk.std           import (
  GenericError,
  GenericWarning,
  Menu,
  TryAndPrint,
  abort,
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
BACKUP_BROWSER_BASE_CMD = (
  get_tool_path('7-Zip', '7z'),
  'a', '-t7z', '-mx=1', '-bso0', '-bse0', '-bsp0',
  )
CONEMU_EXE = get_tool_path('ConEmu', 'ConEmu', check=False)
GPUPDATE_SUCCESS_STRINGS = (
  'Computer Policy update has completed successfully.',
  'User Policy update has completed successfully.',
  )
IN_CONEMU = 'ConEmuPID' in os.environ
PROGRAMFILES_32 = os.environ.get(
  'PROGRAMFILES(X86)', os.environ.get(
    'PROGRAMFILES', r'C:\Program Files (x86)',
    ),
  )
SYSTEMDRIVE = os.environ.get('SYSTEMDRIVE', 'C:')
WHITELIST = '\n'.join((
  str(CONEMU_EXE),
  fr'{PROGRAMFILES_32}\TeamViewer\TeamViewer.exe',
  fr'{PROGRAMFILES_32}\TeamViewer\TeamViewer_Desktop.exe',
  fr'{PROGRAMFILES_32}\TeamViewer\TeamViewer_Note.exe',
  fr'{PROGRAMFILES_32}\TeamViewer\TeamViewer_Service.exe',
  fr'{PROGRAMFILES_32}\TeamViewer\tv_w32.exe',
  fr'{PROGRAMFILES_32}\TeamViewer\tv_x64.exe',
  sys.executable,
  ))
TRY_PRINT = TryAndPrint()
TRY_PRINT.width = WIDTH
TRY_PRINT.verbose = True
for error in ('CalledProcessError', 'FileNotFoundError'):
  TRY_PRINT.add_error(error)


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

  # Fix Function references
  for group, menu in menus.items():
    if group not in base_menus['Groups']:
      continue
    for name in menu.options:
      _function = menu.options[name]['Function']
      if isinstance(_function, str):
        menu.options[name]['Function'] = getattr(
          sys.modules[__name__], _function,
          )

  # Done
  return menus


def end_session():
  """End Auto Repairs session."""
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
    use_autologon_in_autorepairs = reg_read_value(
      'HKCU', AUTO_REPAIR_KEY, 'Use Autologon',
      )
  except FileNotFoundError:
    # Assuming it isn't being used
    use_autologon_in_autorepairs = False
  if use_autologon_in_autorepairs and is_autologon_enabled():
    run_tool('Sysinternals', 'Autologon', '-accepteula', download=True)
    reg_set_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'AutoAdminLogon', '0', 'SZ',
      )

  # Delete Auto Repairs keys
  try:
    reg_delete_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')
  except FileNotFoundError:
    LOG.error('Ending repair session but session not started.')
  try:
    cmd = ['reg', 'delete', fr'HKCU\{AUTO_REPAIR_KEY}', '/f']
    run_program(cmd)
  except CalledProcessError:
    LOG.error('Failed to remove Auto Repairs session settings')


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

  # Run AVRemover
  if not session_started:
    TRY_PRINT.run(
      'Run AVRemover...', run_tool, 'AVRemover', 'AVRemover',
      download=True, msg_good='DONE',
      )

  # Check if autologon is needed
  if not session_started and is_autologon_enabled():
    LOG.warning('Skipping Autologon to preserve current settings.')
    menus['Options'].options['Use Autologon']['Disabled'] = True
    menus['Options'].options['Use Autologon']['Selected'] = False
    reg_set_value('HKCU', AUTO_REPAIR_KEY, 'Use Autologon', 0, 'DWORD')
    save_selection_settings(menus)

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
    TRY_PRINT.run('Killing Explorer...', kill_explorer, msg_good='DONE')
  if options['Use Autologon']['Selected'] and not is_autologon_enabled():
    TRY_PRINT.run(
      'Running Autologon...', run_tool,
      'Sysinternals', 'Autologon', '-accepteula',
      download=True, msg_good='DONE',
      )
    if is_autologon_enabled():
      # Update session settings to remove during end_session()
      reg_set_value('HKCU', AUTO_REPAIR_KEY, 'Use Autologon', 1, 'DWORD')
    else:
      # A password wasn't provided or the account doesn't have one
      options['Use Autologon']['Disabled'] = True
      options['Use Autologon']['Selected'] = False
  if options['Sync Clock']['Selected']:
    TRY_PRINT.run(
      'Syncing Clock...', run_tool, 'Neutron', 'Neutron', msg_good='DONE',
      )
  if options['Run RKill']['Selected']:
    TRY_PRINT.run('Running RKill...', run_rkill, msg_good='DONE')


def init_session(options):
  """Initialize Auto Repairs session."""
  reg_set_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted', 1, 'DWORD')

  # Check timezone
  zone = get_timezone()
  msg = (
    'The timezone is currently set to '
    f'{zone}, switch it to {WINDOWS_TIME_ZONE}?'
    )
  if zone != WINDOWS_TIME_ZONE and ask(msg):
    set_timezone(WINDOWS_TIME_ZONE)

  # Create logon task for Auto Repairs
  cmd = [
    'schtasks', '/create', '/f',
    '/sc', 'ONLOGON',
    '/tn', f'{KIT_NAME_FULL}-AutoRepairs',
    '/rl', 'HIGHEST',
    '/tr', fr'C:\Windows\System32\cmd.exe "/C {sys.executable} {sys.argv[0]}"',
    ]
  if IN_CONEMU:
    cmd[-1] = f'{CONEMU_EXE} -run {sys.executable} {sys.argv[0]}'
  run_program(cmd)

  # One-time tasks
  if options['Run TDSSKiller (once)']['Selected']:
    TRY_PRINT.run('Running TDSSKiller...', run_tdsskiller, msg_good='DONE')
  print('')
  reboot(30)


def is_autologon_enabled():
  """Check if Autologon is enabled, returns bool."""
  auto_admin_logon = False
  try:
    auto_admin_logon = reg_read_value(
      'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
      'AutoAdminLogon',
      )
  except FileNotFoundError:
    # Ignore and assume it's disabled
    pass
  else:
    auto_admin_logon = auto_admin_logon != '0'

  # Done
  return auto_admin_logon


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
  clear_screen()
  print_standard(title)
  print('')
  save_selection_settings(menus)
  print_info('Initializing...')
  init_run(menus['Options'].options)
  save_selection_settings(menus)
  if not session_started:
    init_session(menus['Options'].options)
  print_info('Running repairs')

  # Run repairs
  for group, menu in menus.items():
    if group in ('Main', 'Options'):
      continue
    try:
      run_group(group, menu)
    except KeyboardInterrupt:
      abort()

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
    if isinstance(result['Exception'], GenericWarning):
      kwargs['warning'] = True

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
def auto_adwcleaner(group, name):
  """Run AdwCleaner scan.

  save_settings() is called first since AdwCleaner may kill this script.
  """
  save_settings(group, name, done=True, failed=False, message='DONE')
  result = TRY_PRINT.run('AdwCleaner...', run_adwcleaner, msg_good='DONE')

  # Update with actual results (assuming this script wasn't killed)
  save_settings(group, name, result=result)


def auto_backup_browser_profiles(group, name):
  """Backup browser profiles."""
  backup_all_browser_profiles(use_try_print=True)
  save_settings(group, name, done=True, failed=False, message='DONE')


def auto_backup_power_plans(group, name):
  """Backup power plans."""
  result = TRY_PRINT.run('Backup Power Plans...', export_power_plans)
  save_settings(group, name, result=result)


def auto_backup_registry(group, name):
  """Backup registry."""
  result = TRY_PRINT.run('Backup Registry...', backup_registry)
  save_settings(group, name, result=result)


def auto_bleachbit(group, name):
  """Run BleachBit to clean files."""
  result = TRY_PRINT.run(
    'BleachBit...', run_bleachbit, BLEACH_BIT_CLEANERS, msg_good='DONE',
    )
  save_settings(group, name, result=result)


def auto_chkdsk(group, name):
  """Run CHKDSK repairs."""
  needs_reboot = False
  result = TRY_PRINT.run(f'CHKDSK ({SYSTEMDRIVE})...', run_chkdsk_online)

  # Run offline CHKDSK if required
  if result['Failed'] and 'Repaired' not in result['Message']:
    needs_reboot = True
    result = TRY_PRINT.run(
      f'Scheduling offline CHKDSK ({SYSTEMDRIVE})...',
      run_chkdsk_offline,
      )
    if not result['Failed']:
      # Successfully set dirty bit to force offline check
      # Set result['Failed'] to True because we failed to repair online
      result['Failed'] = True
      result['Message'] = 'Scheduled offline repairs'

  # Done
  save_settings(group, name, result=result)
  if needs_reboot:
    reboot()


def auto_disable_pending_renames(group, name):
  """Disable pending renames."""
  result = TRY_PRINT.run(
    'Disabling pending renames...', disable_pending_renames,
    )
  save_settings(group, name, result=result)


def auto_dism(group, name):
  """Run DISM repairs."""
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


def auto_enable_regback(group, name):
  """Enable RegBack."""
  result = TRY_PRINT.run(
    'Enable RegBack...', reg_set_value, 'HKLM',
    r'System\CurrentControlSet\Control\Session Manager\Configuration Manager',
    'EnablePeriodicBackup', 1, 'DWORD',
    )
  save_settings(group, name, result=result)


def auto_hitmanpro(group, name):
  """Run HitmanPro scan."""
  result = TRY_PRINT.run('HitmanPro...', run_hitmanpro, msg_good='DONE')
  save_settings(group, name, result=result)


def auto_iobit_uninstaller(group, name):
  """Run IO Bit Uninstaller scan."""
  result = TRY_PRINT.run(
    'IO Bit Uninstaller...', run_iobit_uninstaller, msg_good='DONE',
    )
  save_settings(group, name, result=result)


def auto_kvrt(group, name):
  """Run KVRT scan."""
  result = TRY_PRINT.run('KVRT...', run_kvrt, msg_good='DONE')
  save_settings(group, name, result=result)


def auto_microsoft_defender(group, name):
  """Run Microsoft Defender scan."""
  result = TRY_PRINT.run(
    'Microsoft Defender...', run_microsoft_defender, msg_good='DONE',
    )
  save_settings(group, name, result=result)


def auto_reboot(group, name):
  """Reboot the system."""
  save_settings(group, name, done=True, failed=False, message='DONE')
  print('')
  reboot(30)


def auto_remove_power_plan(group, name):
  """Remove custom power plan and set to Balanced."""
  result = TRY_PRINT.run(
    'Remove Custom Power Plan...', remove_custom_power_plan,
    )
  save_settings(group, name, result=result)


def auto_repair_registry(group, name):
  """Delete registry keys with embedded null characters."""
  result = TRY_PRINT.run(
    'Running Registry repairs...', delete_registry_null_keys,
    )
  save_settings(group, name, result=result)


def auto_reset_power_plans(group, name):
  """Reset power plans."""
  result = TRY_PRINT.run('Reset Power Plans...', reset_power_plans)
  save_settings(group, name, result=result)


def auto_reset_proxy(group, name):
  """Reset proxy settings."""
  result = TRY_PRINT.run('Clearing proxy settings...', reset_proxy)
  save_settings(group, name, result=result)


def auto_reset_windows_policies(group, name):
  """Reset Windows policies to defaults."""
  result = TRY_PRINT.run(
    'Resetting Windows policies...', reset_windows_policies,
    )
  save_settings(group, name, result=result)


def auto_restore_uac_defaults(group, name):
  """Restore UAC default settings."""
  result = TRY_PRINT.run('Restoring UAC defaults...', restore_uac_defaults)
  save_settings(group, name, result=result)


def auto_set_custom_power_plan(group, name):
  """Set custom power plan."""
  result = TRY_PRINT.run(
    'Set Custom Power Plan...', create_custom_power_plan,
    enable_sleep=False,
    keep_display_on=True,
    )
  save_settings(group, name, result=result)


def auto_sfc(group, name):
  """Run SFC repairs."""
  result = TRY_PRINT.run('SFC Scan...', run_sfc_scan)
  save_settings(group, name, result=result)


def auto_system_restore_create(group, name):
  """Create System Restore point."""
  result = TRY_PRINT.run(
    'Create System Restore...', create_system_restore_point,
    )
  save_settings(group, name, result=result)


def auto_system_restore_enable(group, name):
  """Enable System Restore."""
  cmd = [
    'powershell', '-Command', 'Enable-ComputerRestore',
    '-Drive', SYSTEMDRIVE,
    ]
  result = TRY_PRINT.run('Enable System Restore...', run_program, cmd=cmd)
  save_settings(group, name, result=result)


def auto_system_restore_set_size(group, name):
  """Set System Restore size."""
  result = TRY_PRINT.run('Set System Restore Size...', set_system_restore_size)
  save_settings(group, name, result=result)


def auto_windows_updates_disable(group, name):
  """Disable Windows Updates."""
  result = TRY_PRINT.run('Disable Windows Updates...', disable_windows_updates)
  if result['Failed']:
    # Reboot and try again?
    reboot()
  save_settings(group, name, result=result)


def auto_windows_updates_enable(group, name):
  """Enable Windows Updates."""
  result = TRY_PRINT.run('Enable Windows Updates...', enable_windows_updates)
  save_settings(group, name, result=result)


def auto_windows_updates_reset(group, name):
  """Reset Windows Updates."""
  result = TRY_PRINT.run('Reset Windows Updates...', reset_windows_updates)
  if result['Failed']:
    # Reboot and try again?
    reboot()
  save_settings(group, name, result=result)


# Misc Functions
def set_backup_path(name, date=False):
  """Set backup path, returns pathlib.Path."""
  return set_local_storage_path('Backups', name, date)


def set_local_storage_path(folder, name, date=False):
  """Get path for local storage, returns pathlib.Path."""
  local_path = get_path_obj(f'{SYSTEMDRIVE}/{KIT_NAME_SHORT}/{folder}/{name}')
  if date:
    local_path = local_path.joinpath(time.strftime('%Y-%m-%d'))
  return local_path


def set_quarantine_path(name, date=False):
  """Set quarantine path, returns pathlib.Path."""
  return set_local_storage_path('Quarantine', name, date)


# Tool Functions
def backup_all_browser_profiles(use_try_print=False):
  """Backup browser profiles for all users."""
  users = get_path_obj(f'{SYSTEMDRIVE}/Users')
  for userprofile in users.iterdir():
    if use_try_print:
      print_info(f'{" "*6}{userprofile.name}')
    backup_browser_profiles(userprofile, use_try_print)


def backup_browser_chromium(backup_path, browser, search_path, use_try_print):
  """Backup Chromium-based browser profile."""
  for item in search_path.iterdir():
    match = re.match(r'^(Default|Profile).*', item.name, re.IGNORECASE)
    if not match:
      continue
    output_path = backup_path.joinpath(f'{browser}-{item.name}.7z')
    if output_path.exists():
      # Assuming backup was already done
      if use_try_print:
        show_data(
          f'{" "*8}{browser} ({item.name})...', 'Backup already exists.',
          color='YELLOW', width=WIDTH,
          )
      continue

    # Backup data
    cmd = [
      *BACKUP_BROWSER_BASE_CMD,
      output_path, item.joinpath('*'), '-x!*Cache*', '-x!Service Worker',
      ]
    if use_try_print:
      TRY_PRINT.run(
        f'{" "*8}{browser} ({item.name})...',
        run_program, cmd, check=False,
        )
    else:
      run_program(cmd, check=False)


def backup_browser_firefox(backup_path, search_path, use_try_print):
  """Backup Firefox browser profile."""
  output_path = backup_path.joinpath('Firefox.7z')

  # Bail early
  if output_path.exists():
    # Assuming backup was already done
    if use_try_print:
      show_data(
        f'{" "*8}Firefox (All)...', 'Backup already exists.',
        color='YELLOW', width=WIDTH,
        )
    return

  # Backup data
  cmd = [
    *BACKUP_BROWSER_BASE_CMD, output_path,
    search_path.joinpath('Profiles'), search_path.joinpath('profiles.ini'),
    ]
  if use_try_print:
    TRY_PRINT.run(f'{" "*8}Firefox (All)...', run_program, cmd, check=False)
  else:
    run_program(cmd, check=False)


def backup_browser_profiles(userprofile, use_try_print=False):
  """Backup browser profiles for userprofile."""
  backup_path = set_backup_path('Browsers', date=True)
  backup_path = backup_path.joinpath(userprofile.name)
  backup_path.mkdir(parents=True, exist_ok=True)

  # Chrome
  search_path = userprofile.joinpath('AppData/Local/Google/Chrome/User Data')
  if search_path.exists():
    backup_browser_chromium(backup_path, 'Chrome', search_path, use_try_print)

  # Edge
  search_path = userprofile.joinpath('AppData/Local/Microsoft/Edge/User Data')
  if search_path.exists():
    backup_browser_chromium(backup_path, 'Edge', search_path, use_try_print)

  # Firefox
  search_path = userprofile.joinpath('AppData/Roaming/Mozilla/Firefox')
  if search_path.joinpath('Profiles').exists():
    backup_browser_firefox(backup_path, search_path, use_try_print)

  # Remove empty folders
  try:
    backup_path.rmdir()
  except OSError:
    # Only looking for empty folders
    pass


def backup_registry():
  """Backup Registry."""
  backup_path = set_backup_path('Registry', date=True)
  backup_path.parent.mkdir(parents=True, exist_ok=True)

  # Check if backup was already done today
  if backup_path.exists():
    raise GenericWarning('Backup already exists.')

  # Backup registry
  run_tool('ERUNT', 'ERUNT', backup_path, 'sysreg', 'curuser', 'otherusers')


def delete_registry_null_keys():
  """Delete registry keys with embedded null characters."""
  run_tool('RegDelNull', 'RegDelNull', '-s', '-y', download=True)


def run_adwcleaner():
  """Run AdwCleaner."""
  settings_path = get_tool_path('AdwCleaner', 'AdwCleaner')
  settings_path = settings_path.with_name('settings')
  out_path = get_path_obj(f'{SYSTEMDRIVE}/AdwCleaner/settings')
  out_path.parent.mkdir(exist_ok=True)
  copy_file(settings_path, out_path, overwrite=True)
  run_tool('AdwCleaner', 'AdwCleaner', download=True)


def run_bleachbit(cleaners, preview=True):
  """Run BleachBit to either clean or preview files."""
  cmd_args = (
    '--preview' if preview else '--clean',
    *cleaners,
    )
  log_path = format_log_path(log_name='BleachBit', timestamp=True, tool=True)
  log_path.parent.mkdir(parents=True, exist_ok=True)
  proc = run_tool('BleachBit', 'bleachbit_console', *cmd_args)

  # Save logs
  log_path.write_text(proc.stdout, encoding='utf-8')
  log_path.with_suffix('.err').write_text(proc.stderr, encoding='utf-8')


def run_hitmanpro():
  """Run HitmanPro scan."""
  log_path = format_log_path(log_name='HitmanPro', timestamp=True, tool=True)
  log_path = log_path.with_suffix('.xml')
  log_path.parent.mkdir(parents=True, exist_ok=True)
  cmd_args = ['/scanonly', f'/log={log_path}']
  run_tool('HitmanPro', 'HitmanPro', *cmd_args, download=True)


def run_iobit_uninstaller():
  """Run IO Bit Uninstaller."""
  run_tool('IObitUninstallerPortable', 'IObitUninstallerPortable', cbin=True)


def run_kvrt():
  """Run KVRT scan."""
  log_path = format_log_path(log_name='KVRT', timestamp=True, tool=True)
  log_path.parent.mkdir(parents=True, exist_ok=True)
  quarantine_path = set_quarantine_path('KVRT')
  quarantine_path.mkdir(parents=True, exist_ok=True)
  cmd_args = (
    '-accepteula',
    '-d', str(quarantine_path),
    '-dontencrypt', '-fixednames',
    '-processlevel', '1',
    '-custom', SYSTEMDRIVE,
    '-silent', '-adinsilent',
    )

  # Run in new pane
  if IN_CONEMU:
    download_tool('KVRT', 'KVRT')
    kvrt_path = get_tool_path('KVRT', 'KVRT')
    tmp_file = fr'{os.environ.get("TMP")}\run_kvrt.cmd'
    with open(tmp_file, 'w', encoding='utf-8') as _f:
      _f.write('@echo off\n')
      _f.write(f'"{kvrt_path}" {" ".join(cmd_args)}\n')
    cmd = ('cmd', '/c', tmp_file, '-new_console:nb', '-new_console:s33V')
    run_program(cmd, check=False)
    sleep(1)
    wait_for_procs('KVRT.exe')
    return

  # Run in background
  proc = run_tool('KVRT', 'KVRT', *cmd_args, download=True)
  log_path.write_text(proc.stdout, encoding='utf-8')


def run_microsoft_defender(full=True):
  """Run Microsoft Defender scan."""
  reg_key = r'Software\Microsoft\Windows Defender'

  def _get_defender_path():
    install_path = reg_read_value('HKLM', reg_key, 'InstallLocation')
    return fr'{install_path}\MpCmdRun.exe'

  log_path = format_log_path(
    log_name='Microsoft Defender', timestamp=True, tool=True,
    )
  log_path.parent.mkdir(parents=True, exist_ok=True)

  # Get MS Defender status
  ## NOTE: disabled may be set to an int instead of bool
  ##       This is fine because we're just checking if it's enabled.
  disabled = bool(reg_read_value('HKLM', reg_key, 'DisableAntiSpyware'))
  disabled = disabled or reg_read_value('HKLM', reg_key, 'DisableAntiVirus')
  try:
    passive_mode = reg_read_value('HKLM', reg_key, 'PassiveMode') == 2
  except FileNotFoundError:
    # The registry key may not exist so this is fine
    passive_mode = False
  if disabled and not passive_mode:
    raise GenericError('Defender is disabled.')

  # Update signatures
  defender_path = _get_defender_path()
  cmd = (defender_path, '-SignatureUpdate')
  proc = run_program(cmd, check=False)
  sleep(2)
  if proc.returncode > 0:
    LOG.warning('Failed to update Defender signatures')

  # Update defender path in case it changed after the update
  defender_path = _get_defender_path()

  # Run scan
  cmd = (defender_path, '-Scan', '-ScanType', '2' if full else '1')
  proc = run_program(cmd, check=False)
  log_path.write_text(proc.stdout, encoding='utf-8')
  if proc.returncode > 0:
    raise GenericError('Failed to run scan or clean items.')


def run_rkill():
  """Run RKill scan."""
  log_path = format_log_path(log_name='RKill', timestamp=True, tool=True)
  log_path.parent.mkdir(parents=True, exist_ok=True)
  whitelist_path = log_path.with_suffix('.wl')
  whitelist_path.write_text(WHITELIST, encoding='utf-8')
  cmd_args = (
    '-l', log_path,
    '-w', whitelist_path,
    '-s',
    )
  run_tool('RKill', 'RKill', *cmd_args, download=True)


def run_tdsskiller():
  """Run TDSSKiller scan."""
  log_path = format_log_path(log_name='TDSSKiller', timestamp=True, tool=True)
  log_path.parent.mkdir(parents=True, exist_ok=True)
  quarantine_path = set_quarantine_path('TDSSKiller')
  quarantine_path.mkdir(parents=True, exist_ok=True)
  cmd_args = (
    '-accepteula',
    '-accepteulaksn',
    '-l', log_path,
    '-qpath', quarantine_path,
    '-qsus',
    '-dcexact',
    '-silent',
    )
  run_tool('TDSSKiller', 'TDSSKiller', *cmd_args, download=True)


# OS Built-in Functions
def create_custom_power_plan(enable_sleep=True, keep_display_on=False):
  """Create new power plan and set as active."""
  custom_guid = POWER_PLANS['Custom']
  sleep_timeouts = POWER_PLAN_SLEEP_TIMEOUTS['High Performance']
  if enable_sleep:
    sleep_timeouts = POWER_PLAN_SLEEP_TIMEOUTS['Balanced']

  # Duplicate High Performance plan
  cmd = [
    'powercfg', '-DuplicateScheme',
    POWER_PLANS['High Performance'], custom_guid,
    ]
  proc = run_program(cmd, check=False)
  if proc.returncode and 'GUID already exists' not in proc.stderr:
    LOG.error("Failed to create custom power plan.\n  Details: %s", proc)

  # Change the name
  cmd = [
    'powercfg', '-ChangeName', custom_guid,
    CUSTOM_POWER_PLAN_NAME, CUSTOM_POWER_PLAN_DESC,
    ]
  run_program(cmd)

  # Set as active plan
  cmd = ['powercfg', '-SetActive', custom_guid]
  run_program(cmd)

  # Keep the display on
  if keep_display_on:
    for setting in ('monitor-timeout-ac', 'monitor-timeout-dc'):
      cmd = ['powercfg', '-Change', setting, '0']
      run_program(cmd)

  # Set CPU min state
  for arg in ('-SetacValueIndex', '-SetdcValueIndex'):
    cmd = [
      'powercfg', arg, custom_guid, 'SUB_PROCESSOR', 'PROCTHROTTLEMIN', '5',
      ]
    run_program(cmd)

  # Set sleep values
  for arg, value in zip(
      ('-SetacValueIndex', '-SetdcValueIndex'), sleep_timeouts):
    cmd = [
      'powercfg', arg, custom_guid, 'SUB_SLEEP', 'STANDBYIDLE', value,
      ]
    run_program(cmd)


def create_system_restore_point():
  """Create System Restore point."""
  cmd = [
    'powershell', '-Command', 'Checkpoint-Computer',
    '-Description', f'{KIT_NAME_FULL}-AutoRepairs',
    ]
  too_recent = (
    'WARNING: A new system restore point cannot be created'
    'because one has already been created within the past'
    )
  proc = run_program(cmd)
  if too_recent in proc.stdout:
    raise GenericWarning('Skipped, a restore point was created too recently')


def disable_pending_renames():
  """Disable pending renames."""
  reg_set_value(
    'HKLM', r'SYSTEM\CurrentControlSet\Control\Session Manager',
    'PendingFileRenameOperations', [], 'MULTI_SZ',
    )


def disable_windows_updates():
  """Disable and stop Windows Updates."""
  disable_service('wuauserv')
  stop_service('wuauserv')


def enable_windows_updates():
  """Enable Windows Updates."""
  enable_service('wuauserv', 'demand')


def export_power_plans():
  """Export existing power plans."""
  backup_path = set_backup_path('Power Plans', date=True)

  # Bail early
  if backup_path.exists():
    raise GenericWarning('Backup already exists.')

  # Get powercfg data
  backup_path.mkdir(parents=True, exist_ok=True)
  cmd = ['powercfg', '/L']
  proc = run_program(cmd)
  plans = {}

  # Get plans
  for line in proc.stdout.splitlines():
    line = line.strip()
    match = re.match(r'^Power Scheme GUID: (.{36})\s+\((.*)\)\s*(\*?)', line)
    if match:
      name = match.group(2)
      if match.group(3):
        name += ' (Default)'
      plans[name] = match.group(1)

  # Backup plans to disk
  for name, guid in plans.items():
    out_path = backup_path.joinpath(f'{name}.pow')
    cmd = ['powercfg', '-export', out_path, guid]
    run_program(cmd)


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


def remove_custom_power_plan(high_performance=False):
  """Remove custom power plan and set to a built-in plan.

  If high_performance is True then set to High Performance and set
  min CPU state to 5% otherwise set to Balanced with default settings.
  """
  power_guid = POWER_PLANS['Balanced']
  if high_performance:
    power_guid = POWER_PLANS['High Performance']

  # Set active plan
  cmd = ['powercfg', '-SetActive', power_guid]
  run_program(cmd)

  # Delete custom power plan (if present)
  cmd = ['powercfg', '-Delete', POWER_PLANS['Custom']]
  run_program(cmd, check=False)

  # Set CPU min state (if needed)
  if high_performance:
    for arg in ('-SetacValueIndex', '-SetdcValueIndex'):
      cmd = [
        'powercfg', arg, power_guid, 'SUB_PROCESSOR', 'PROCTHROTTLEMIN', '5',
        ]
      run_program(cmd)


def reset_power_plans():
  """Reset power plans to their default settings."""
  cmd = ['powercfg', '-RestoreDefaultSchemes']
  run_program(cmd)


def reset_proxy():
  """Reset WinHTTP proxy settings."""
  cmd = ['netsh', 'winhttp', 'reset', 'proxy']
  proc = run_program(cmd, check=False)

  # Check result
  if 'Direct access (no proxy server)' not in proc.stdout:
    raise GenericError('Failed to reset proxy settings.')


def reset_windows_policies():
  """Reset Windows policies to defaults."""
  cmd = ['gpupdate', '/force']
  proc = run_program(cmd, check=False)

  # Check result
  if not all(_s in proc.stdout for _s in GPUPDATE_SUCCESS_STRINGS):
    raise GenericError('Failed to reset one or more policies.')


def reset_windows_updates():
  """Reset Windows Updates."""
  system_root = os.environ.get('SYSTEMROOT', 'C:/Windows')
  src_path = f'{system_root}/SoftwareDistribution'
  dest_path = non_clobber_path(f'{src_path}.old')
  try:
    rename_item(src_path, dest_path)
    delete_folder(dest_path, force=True)
  except FileNotFoundError:
    # Ignore
    pass


def restore_uac_defaults():
  """Restore UAC default settings."""
  settings = REG_UAC_DEFAULTS_WIN10
  if OS_VERSION in (7, 8, 8.1):
    settings = REG_UAC_DEFAULTS_WIN7

  reg_write_settings(settings)


def run_chkdsk_offline():
  """Set filesystem 'dirty bit' to force a CHKDSK during startup."""
  cmd = ['fsutil', 'dirty', 'set', SYSTEMDRIVE]
  proc = run_program(cmd, check=False)

  # Check result
  if proc.returncode > 0:
    raise GenericError('Failed to set dirty bit.')


def run_chkdsk_online():
  """Run CHKDSK.

  NOTE: If run on Windows 8+ online repairs are attempted.
  """
  cmd = ['CHKDSK', SYSTEMDRIVE]
  if OS_VERSION >= 8:
    cmd.extend(['/scan', '/perf'])
  if IN_CONEMU:
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
  conemu_args = ['-new_console:nb', '-new_console:s33V'] if IN_CONEMU else []

  # Bail early
  if OS_VERSION < 8:
    raise GenericWarning('Unsupported OS')

  # Run (repair) scan
  log_path = format_log_path(
    log_name=f'DISM_{"Restore" if repair else "Scan"}Health',
    timestamp=True, tool=True,
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
  log_path = format_log_path(
    log_name='DISM_CheckHealth.log', timestamp=True, tool=True,
    )
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
  log_path = format_log_path(log_name='SFC', timestamp=True, tool=True)
  err_path = log_path.with_suffix('.err')

  # Run SFC
  proc = run_program(cmd, check=False, encoding='utf-16le')

  # Save output
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'a', encoding='utf-8') as _f:
    _f.write(proc.stdout)
  with open(err_path, 'a', encoding='utf-8') as _f:
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


def set_system_restore_size(size=8):
  """Set System Restore size."""
  cmd = [
    'vssadmin', 'Resize', 'ShadowStorage',
    f'/On={SYSTEMDRIVE}', f'/For={SYSTEMDRIVE}', f'/MaxSize={size}%',
    ]
  run_program(cmd, pipe=False, stderr=DEVNULL, stdout=DEVNULL)


def start_explorer():
  """Start Explorer."""
  popen_program(['explorer.exe'])


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
