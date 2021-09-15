"""WizardKit: Setup - Windows"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import platform
import re
import sys
import time

from subprocess       import CalledProcessError, DEVNULL

from wk.cfg.main      import KIT_NAME_FULL, KIT_NAME_SHORT
from wk.exe           import (
  get_procs,
  run_program,
  popen_program,
  wait_for_procs,
  )
from wk.io            import (
  delete_folder,
  get_path_obj,
  non_clobber_path,
  rename_item,
  )
from wk.kit.tools     import (
  ARCH,
  download_tool,
  extract_tool,
  get_tool_path,
  run_tool,
  )
from wk.log           import format_log_path, update_log_path
from wk.os.win        import (
  reg_delete_value,
  reg_read_value,
  reg_set_value,
  reg_write_settings,
  disable_service,
  enable_service,
  stop_service,
  )
from wk.repairs.win   import (
  backup_all_browser_profiles,
  backup_registry,
  create_custom_power_plan,
  create_system_restore_point,
  enable_windows_updates,
  export_power_plans,
  reset_power_plans,
  set_system_restore_size,
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
CONEMU_EXE = get_tool_path('ConEmu', 'ConEmu', check=False)
IN_CONEMU = 'ConEmuPID' in os.environ
MENU_PRESETS = Menu()
PROGRAMFILES_32 = os.environ.get(
  'PROGRAMFILES(X86)', os.environ.get(
    'PROGRAMFILES', r'C:\Program Files (x86)',
    ),
  )
OS_VERSION = float(platform.win32_ver()[0])
SYSTEMDRIVE = os.environ.get('SYSTEMDRIVE', 'C:')
WIDTH = 50
TRY_PRINT = TryAndPrint()
TRY_PRINT.width = WIDTH
TRY_PRINT.verbose = True
for error in ('CalledProcessError', 'FileNotFoundError'):
  TRY_PRINT.add_error(error)


# Auto Setup
def build_menus(base_menus, title, presets):
  """Build menus, returns dict."""
  menus = {}
  menus['Main'] = Menu(title=f'{title}\n{color_string("Main Menu", "GREEN")}')

  # Main Menu
  for entry in base_menus['Actions']:
    menus['Main'].add_action(entry.name, entry.details)
  for group in base_menus['Groups']:
    menus['Main'].add_option(group, {'Selected': True})

  # Run groups
  for group, entries in base_menus['Groups'].items():
    menus[group] = Menu(title=f'{title}\n{color_string(group, "GREEN")}')
    for entry in entries:
      menus[group].add_option(entry.name, entry.details)
    menus[group].add_action('All')
    menus[group].add_action('None')
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

  # Update presets Menu
  MENU_PRESETS.title = f'{title}\n{color_string("Load Preset", "GREEN")}'
  MENU_PRESETS.add_option('Default')
  for name in presets:
    MENU_PRESETS.add_option(name)
  MENU_PRESETS.add_action('Main Menu')
  MENU_PRESETS.add_action('Quit')
  MENU_PRESETS.update()

  # Done
  return menus


def load_preset(menus, presets):
  """Load menu settings from preset."""
  selection = MENU_PRESETS.simple_select()

  # Exit early
  if 'Main Menu' in selection:
    return
  if 'Quit' in selection:
    raise SystemExit

  # Default case
  if 'Default' in selection:
    for menu in menus.values():
      for name in menu.options:
        menu.options[name]['Selected'] = True
    return

  # Load preset
  preset = presets[selection[0]]
  for group, menu in menus.items():
    group_enabled = group in preset
    for name in menu.options:
      value = group_enabled and name in preset[group]
      menu.options[name]['Selected'] = value


def run_auto_setup(base_menus, presets):
  """Run Auto Setup."""
  update_log_path(dest_name='Auto Setup', timestamp=True)
  title = f'{KIT_NAME_FULL}: Auto Setup'
  clear_screen()
  set_title(title)
  print_info(title)
  print('')

  # Generate menus
  print_standard('Initializing...')
  menus = build_menus(base_menus, title, presets)

  # Show Menu
  show_main_menu(base_menus, menus, presets)

  # Start setup
  clear_screen()
  print_standard(title)
  print('')
  print_info('Running setup')

  # Run setup
  for group, menu in menus.items():
    if group in ('Main', 'Options'):
      continue
    try:
      run_group(group, menu)
    except KeyboardInterrupt:
      abort()

  # Done
  print_info('Done')
  pause('Press Enter to exit...')


def run_group(group, menu):
  """Run entries in group if appropriate."""
  print_info(f'  {group}')
  for name, details in menu.options.items():
    name_str = strip_colors(name)

    # Not selected
    if not details.get('Selected', False):
      show_data(f'{name_str}...', 'Skipped', 'YELLOW', width=WIDTH)
      continue

    # Selected
    details['Function']()


def show_main_menu(base_menus, menus, presets):
  """Show main menu and handle actions."""
  while True:
    update_main_menu(menus)
    selection = menus['Main'].simple_select(update=False)
    if selection[0] in base_menus['Groups'] or selection[0] == 'Options':
      show_sub_menu(menus[selection[0]])
    if selection[0] == 'Load Preset':
      load_preset(menus, presets)
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

    # Select all or none
    value = 'All' in selection
    for name in menu.options:
      if not menu.options[name].get('Disabled', False):
        menu.options[name]['Selected'] = value


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
def auto_backup_registry():
  """Backup registry."""
  TRY_PRINT.run('Backup Registry...', backup_registry)


def auto_backup_browser_profiles():
  """Backup browser profiles."""
  backup_all_browser_profiles(use_try_print=True)


def auto_backup_power_plans():
  """Backup power plans."""
  TRY_PRINT.run('Backup Power Plans...', export_power_plans)


def auto_reset_power_plans():
  """Reset power plans."""
  TRY_PRINT.run('Reset Power Plans...', reset_power_plans)


def auto_set_custom_power_plan():
  """Set custom power plan."""
  TRY_PRINT.run('Set Custom Power Plan...', create_custom_power_plan)


def auto_enable_regback():
  """Enable RegBack."""
  TRY_PRINT.run(
    'Enable RegBack...', reg_set_value, 'HKLM',
    r'System\CurrentControlSet\Control\Session Manager\Configuration Manager',
    'EnablePeriodicBackup', 1, 'DWORD',
    )


def auto_system_restore_enable():
  """Enable System Restore."""
  cmd = [
    'powershell', '-Command', 'Enable-ComputerRestore',
    '-Drive', SYSTEMDRIVE,
    ]
  TRY_PRINT.run('Enable System Restore...', run_program, cmd=cmd)


def auto_system_restore_set_size():
  """Set System Restore size."""
  TRY_PRINT.run('Set System Restore Size...', set_system_restore_size)


def auto_system_restore_create():
  """Create System Restore point."""
  TRY_PRINT.run('Create System Restore...', create_system_restore_point)


def auto_windows_updates_enable():
  """Enable Windows Updates."""
  TRY_PRINT.run('Enable Windows Updates...', enable_windows_updates)


# Auto Setup: Wrapper Functions
def auto_install_vcredists():
  """Install latest supported Visual C++ runtimes."""
  TRY_PRINT.run('Visual C++ Runtimes...', install_vcredists)

# Install Functions
def install_vcredists():
  """Install latest supported Visual C++ runtimes."""
  for year in (2012, 2013, 2019):
    cmd_args = ['/install', '/passive', '/norestart']
    if year == 2012:
      cmd_args.pop(0)
    name = f'VCRedist_{year}_x32'
    download_tool('VCRedist', name)
    installer = get_tool_path('VCRedist', name)
    run_program([installer, *cmd_args])
    if ARCH == '64':
      name = f'{name[:-2]}64'
      download_tool('VCRedist', name)
      installer = get_tool_path('VCRedist', name)
      run_program([installer, *cmd_args])

# Misc Functions
## TODO?

# Tool Functions
## TODO?

# OS Built-in Functions
## TODO?

if __name__ == '__main__':
  print("This file is not meant to be called directly.")
