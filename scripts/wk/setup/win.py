"""WizardKit: Setup - Windows"""
# vim: sts=2 sw=2 ts=2

import configparser
import logging
import json
import os
import platform
import re
import sys

from wk.cfg.main      import KIT_NAME_FULL
from wk.exe           import kill_procs, run_program, popen_program
from wk.io            import case_insensitive_path, get_path_obj
from wk.kit.tools     import (
  ARCH,
  download_tool,
  extract_archive,
  extract_tool,
  find_kit_dir,
  get_tool_path,
  run_tool,
  )
from wk.log           import format_log_path, update_log_path
from wk.std           import (
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
if platform.system() == 'Windows':
  from wk.os.win        import (
    activate_with_bios,
    reg_read_value,
    reg_set_value,
    reg_write_settings,
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
else:
  # Workaround to allow basic testing under non-Windows environments
  def no_op(*args, **kwargs): # pylint: disable=unused-argument
    """No-op function."""
  # wk.os.win
  activate_with_bios = no_op
  reg_read_value = no_op
  reg_set_value = no_op
  reg_write_settings = no_op
  # wk.repairs.win
  backup_all_browser_profiles = no_op
  backup_registry = no_op
  create_custom_power_plan = no_op
  create_system_restore_point = no_op
  enable_windows_updates = no_op
  export_power_plans = no_op
  reset_power_plans = no_op
  set_system_restore_size = no_op


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
BROWSER_PATHS = {
  # Relative to PROGRAMFILES_64, PROGRAMFILES_32, LOCALAPPDATA (in that order)
  'Google Chrome': 'Google/Chrome/Application/chrome.exe',
  'Mozilla Firefox': 'Mozilla Firefox/firefox.exe',
  'Microsoft Edge': 'Microsoft/Edge/Application/msedge.exe',
  'Opera': 'Opera/launcher.exe',
  }
CONEMU_EXE = get_tool_path('ConEmu', 'ConEmu', check=False)
IN_CONEMU = 'ConEmuPID' in os.environ
LIBREOFFICE_XCU_DATA = '''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.presentation.PresentationDocument']"><prop oor:name="ooSetupFactoryDefaultFilter" oor:op="fuse"><value>Impress MS PowerPoint 2007 XML</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.sheet.SpreadsheetDocument']"><prop oor:name="ooSetupFactoryDefaultFilter" oor:op="fuse"><value>Calc MS Excel 2007 XML</value></prop></item>
<item oor:path="/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory['com.sun.star.text.TextDocument']"><prop oor:name="ooSetupFactoryDefaultFilter" oor:op="fuse"><value>MS Word 2007 XML</value></prop></item>
<item oor:path="/org.openoffice.Office.Common/Save/Document"><prop oor:name="WarnAlienFormat" oor:op="fuse"><value>false</value></prop></item>
</oor:items>
'''
MENU_PRESETS = Menu()
OS_VERSION = -1
if platform.system() == 'Windows':
  OS_VERSION = float(platform.win32_ver()[0])
PROGRAMFILES_32 = os.environ.get(
  'PROGRAMFILES(X86)', os.environ.get(
    'PROGRAMFILES', r'C:\Program Files (x86)',
    ),
  )
PROGRAMFILES_64 = os.environ.get(
  'PROGRAMW6432', os.environ.get(
    'PROGRAMFILES', r'C:\Program Files',
    ),
  )
REG_CHROME_UBLOCK_ORIGIN = {
  'HKLM': {
    r'Software\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm': (
      ('update_url', 'https://clients2.google.com/service/update2/crx', 'SZ', '32'),
      )
    },
  }
REG_WINDOWS_EXPLORER = {
  # pylint: disable=line-too-long
  'HKLM': {
    # Disable Location Tracking
    r'Software\Microsoft\Windows NT\CurrentVersion\Sensor\Overrides\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}': (
      ('SensorPermissionState', 0, 'DWORD'),
      ),
    r'System\CurrentControlSet\Services\lfsvc\Service\Configuration': (
      ('Status', 0, 'DWORD'),
      ),
    # Disable Telemetry
    r'Software\Microsoft\Windows\CurrentVersion\Policies\DataCollection': (
      ('AllowTelemetry', 0, 'DWORD'),
      ('AllowTelemetry', 0, 'DWORD', '32'),
      ),
    r'Software\Policies\Microsoft\Windows\DataCollection': (
      ('AllowTelemetry', 0, 'DWORD'),
      ),
    # Disable Wi-Fi Sense
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowWiFiHotSpotReporting': (
      ('Value', 0, 'DWORD'),
      ),
    r'Software\Microsoft\PolicyManager\default\WiFi\AllowAutoConnectToWiFiSenseHotspots': (
      ('Value', 0, 'DWORD'),
      ),
    },
  'HKCU': {
    # Desktop theme (<= v1809 default)
    r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize': {
      ('AppsUseLightTheme', 1, 'DWORD'),
      ('SystemUsesLightTheme', 0, 'DWORD'),
      },
    # Disable features
    r'Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager': {
      ('SilentInstalledAppsEnabled', 0, 'DWORD'),
      # Tips and Tricks
      ('SoftLandingEnabled ', 0, 'DWORD'),
      ('SubscribedContent-338389Enabled', 0, 'DWORD'),
      },
    # File Explorer
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced': {
      # Change default Explorer view to "Computer"
      ('LaunchTo', 1, 'DWORD'),
      ('SeparateProcess', 1, 'DWORD'),
      },
    # Hide People bar
    r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People': {
      ('PeopleBand', 0, 'DWORD'),
      },
    # Hide Search button / box
    r'Software\Microsoft\Windows\CurrentVersion\Search': {
      ('SearchboxTaskbarMode', 1, 'DWORD'),
      },
    },
  }
REG_OPEN_SHELL_SETTINGS = {
  'HKCU': {
    r'Software\OpenShell\StartMenu': (
      ('ShowedStyle2', 1, 'DWORD'),
      ),
    r'Software\OpenShell\StartMenu\Settings': (
      ('MenuStyle', 'Win7', 'SZ'),
      ('RecentPrograms', 'Recent', 'SZ'),
      ('SkinW7', 'Fluent-Metro', 'SZ'),
      ('SkinVariationW7', '', 'SZ'),
      ('SkipMetro', 1, 'DWORD'),
      (
        'SkinOptionsW7',
        [
          # NOTE: Seems to need all options specified to work?
          'DARK_MAIN=1', 'METRO_MAIN=0', 'LIGHT_MAIN=0', 'AUTOMODE_MAIN=0',
          'DARK_SUBMENU=0', 'METRO_SUBMENU=0', 'LIGHT_SUBMENU=0', 'AUTOMODE_SUBMENU=1',
          'SUBMENU_SEPARATORS=1', 'DARK_SEARCH=0', 'METRO_SEARCH=0', 'LIGHT_SEARCH=1',
          'AUTOMODE_SEARCH=0', 'SEARCH_FRAME=1', 'SEARCH_COLOR=0', 'SMALL_SEARCH=0',
          'MODERN_SEARCH=1', 'SEARCH_ITALICS=0', 'NONE=0', 'SEPARATOR=0',
          'TWO_TONE=1', 'CLASSIC_SELECTOR=1', 'HALF_SELECTOR=0', 'CURVED_MENUSEL=1',
          'CURVED_SUBMENU=0', 'SELECTOR_REVEAL=0', 'TRANSPARENT=0', 'OPAQUE_SUBMENU=1',
          'OPAQUE_MENU=0', 'OPAQUE=0', 'STANDARD=1', 'SMALL_MAIN2=0',
          'SMALL_ICONS=0', 'COMPACT_SUBMENU=0', 'PRESERVE_MAIN2=0', 'LESS_PADDING=0',
          'EXTRA_PADDING=1', '24_PADDING=0', 'LARGE_PROGRAMS=0', 'TRANSPARENT_SHUTDOWN=0',
          'OUTLINE_SHUTDOWN=0', 'BUTTON_SHUTDOWN=1', 'EXPERIMENTAL_SHUTDOWN=0', 'LARGE_FONT=0',
          'CONNECTED_BORDER=1', 'FLOATING_BORDER=0', 'LARGE_SUBMENU=0', 'LARGE_LISTS=0',
          'THIN_MAIN2=0', 'EXPERIMENTAL_MAIN2=1', 'USER_IMAGE=1', 'USER_OUTSIDE=0',
          'SCALING_USER=1', '56=0', '64=0', 'TRANSPARENT_USER=0',
          'UWP_SCROLLBAR=1', 'MODERN_SCROLLBAR=0', 'OLD_ICONS=0', 'NEW_ICONS=1',
          'SMALL_ARROWS=0', 'ICON_FRAME=0', 'SEARCH_SEPARATOR=0', 'NO_PROGRAMS_BUTTON=0',
          ],
        'MULTI_SZ',
        ),
      ),
    },
  }
REG_UAC_DEFAULTS_WIN7 = {
  'HKLM': {
    r'Software\Microsoft\Windows\CurrentVersion\Policies\System': (
      ('ConsentPromptBehaviorAdmin', 5, 'DWORD'),
      ('EnableLUA', 1, 'DWORD'),
      ('PromptOnSecureDesktop', 1, 'DWORD'),
      ),
    },
  }
REG_UAC_DEFAULTS_WIN10 = {
  'HKLM': {
    r'Software\Microsoft\Windows\CurrentVersion\Policies\System': (
      ('ConsentPromptBehaviorAdmin', 5, 'DWORD'),
      ('ConsentPromptBehaviorUser', 3, 'DWORD'),
      ('EnableInstallerDetection', 1, 'DWORD'),
      ('EnableLUA', 1, 'DWORD'),
      ('EnableVirtualization', 1, 'DWORD'),
      ('PromptOnSecureDesktop', 1, 'DWORD'),
      ),
    },
  }
SYSTEMDRIVE = os.environ.get('SYSTEMDRIVE', 'C:')
WIDTH = 50
TRY_PRINT = TryAndPrint()
TRY_PRINT.width = WIDTH
TRY_PRINT.verbose = True
for error in ('CalledProcessError', 'FileNotFoundError'):
  TRY_PRINT.add_error(error)
UBLOCK_ORIGIN_URLS = {
  # pylint: disable=line-too-long
  'Google Chrome':    'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm',
  'Microsoft Edge':   'https://microsoftedge.microsoft.com/addons/detail/ublock-origin/odfafepnkmbhccpbejgmiehpchacaeak',
  'Mozilla Firefox':  'https://addons.mozilla.org/addon/ublock-origin/',
  'Opera':            'https://addons.opera.com/extensions/details/ublock/',
  }


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


def auto_enable_bsod_minidumps():
  """Enable saving minidumps during BSoDs."""
  TRY_PRINT.run('Enable BSoD mini dumps...', enable_bsod_minidumps)


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
def auto_activate_windows():
  """Attempt to activate Windows using BIOS key."""
  TRY_PRINT.run('Windows Activation...', activate_with_bios)


def auto_config_explorer():
  """Configure Windows Explorer and restart the process."""
  TRY_PRINT.run('Windows Explorer...', config_explorer)


def auto_config_open_shell():
  """Configure Open Shell."""
  TRY_PRINT.run('Open Shell...', reg_write_settings, REG_OPEN_SHELL_SETTINGS)


def auto_disable_chrome_notifications():
  """Disable notifications in Google Chrome."""
  TRY_PRINT.run('Chrome Notifications...', disable_chrome_notifications)


def auto_enable_ublock_origin():
  """Enable uBlock Origin in supported browsers."""
  prompt = '    Press Enter to continue...'
  TRY_PRINT.run(
    'uBlock Origin...', enable_ublock_origin, msg_good='STARTED',
    )
  print(prompt, end='', flush=True)
  pause('')

  # Move cursor to beginning of the previous line and clear prompt
  print(f'\033[F\r{" "*len(prompt)}\r', end='', flush=True)


def auto_install_firefox():
  """Install Firefox."""
  TRY_PRINT.run('Firefox...', install_firefox)


def auto_install_libreoffice():
  """Install LibreOffice.

  NOTE: It is assumed that auto_install_vcredists() will be run
        before this function to satisfy the vcredist=False usage.
  """
  TRY_PRINT.run('LibreOffice...', install_libreoffice, vcredist=False)


def auto_install_open_shell():
  """Install Open Shell."""
  TRY_PRINT.run('Open Shell...', install_open_shell)


def auto_install_software_bundle():
  """Install standard software bundle."""
  TRY_PRINT.run('Software Bundle...', install_software_bundle)


def auto_install_vcredists():
  """Install latest supported Visual C++ runtimes."""
  TRY_PRINT.run('Visual C++ Runtimes...', install_vcredists)


def auto_restore_default_uac():
  """Restore default UAC settings."""
  TRY_PRINT.run('User Account Control...', restore_default_uac)


def auto_windows_temp_fix():
  """Restore default ACLs for Windows\\Temp."""
  TRY_PRINT.run(r'Windows\Temp fix...', fix_windows_temp)




# Configure Functions
def config_explorer():
  """Configure Windows Explorer and restart the process."""
  reg_write_settings(REG_WINDOWS_EXPLORER)
  kill_procs('explorer.exe', force=True)
  popen_program(['explorer.exe'])


def disable_chrome_notifications():
  """Disable notifications in Google Chrome."""
  defaults_key = 'default_content_setting_values'
  profiles = []
  search_path = case_insensitive_path(
    f'{os.environ.get("LOCALAPPDATA")}/Google/Chrome/User Data',
    )

  # Bail early
  if not search_path:
    raise GenericWarning('No profiles detected.')

  # Close any running instances of Chrome
  kill_procs('chrome.exe', force=True)

  # Build list of profiles
  for item in search_path.iterdir():
    if not item.is_dir():
      continue

    if re.match(r'^(Default|Profile).*', item.name, re.IGNORECASE):
      profiles.append(item)

  # Bail if no profiles were detected
  if not profiles:
    raise GenericWarning('No profiles detected.')

  # Set notifications preference
  for profile in profiles:
    pref_file = profile.joinpath('Preferences')
    if not pref_file.exists():
      continue

    # Update config
    pref_data = json.loads(pref_file.read_text())
    if defaults_key not in pref_data['profile']:
      pref_data['profile'][defaults_key] = {}
    pref_data['profile'][defaults_key]['notifications'] = 2

    # Save file
    pref_file.write_text(json.dumps(pref_data, separators=(',', ':')))


def enable_bsod_minidumps():
  """Enable saving minidumps during BSoDs."""
  cmd = ['wmic', 'RECOVEROS', 'set', 'DebugInfoType', '=', '3']
  run_program(cmd)


def enable_ublock_origin():
  """Enable uBlock Origin in supported browsers."""
  base_paths = [
    PROGRAMFILES_64, PROGRAMFILES_32, os.environ.get('LOCALAPPDATA'),
    ]
  cmds = []

  # Add Google Chrome registry entries
  reg_write_settings(REG_CHROME_UBLOCK_ORIGIN)

  # Build cmds list
  for browser, rel_path in BROWSER_PATHS.items():
    browser_path = None
    for base_path in base_paths:
      try:
        browser_path = case_insensitive_path(f'{base_path}/{rel_path}')
      except FileNotFoundError:
        # Ignore missing browsers
        continue
      else:
        # Found a match, skip checking the rest
        break
    if browser_path:
      cmds.append([browser_path, UBLOCK_ORIGIN_URLS[browser]])

  # Open detected browsers
  for cmd in cmds:
    popen_program(cmd)


def fix_windows_temp():
  """Restore default permissions for Windows\\Temp."""
  permissions = (
    'Users:(CI)(X,WD,AD)',
    'Administrators:(OI)(CI)(F)',
    )
  for _p in permissions:
    cmd = ['icacls', fr'{SYSTEMDRIVE}\Windows\Temp', '/grant:r', _p, '/T']
    run_program(cmd)


def restore_default_uac():
  """Restore default UAC settings."""
  settings = REG_UAC_DEFAULTS_WIN10
  if OS_VERSION != 10:
    settings = REG_UAC_DEFAULTS_WIN7

  reg_write_settings(settings)


# Install Functions
def install_firefox():
  """Install Firefox.

  As far as I can tell if you use the EXE installers then it will use
  the same installation directory as the installed version.  As such a
  32-bit installation could be upgraded to a 64-bit one and still use
  %PROGRAMFILES(X86)%  However, if a 64-bit MSI installer is used then
  it ignores the 32-bit directory and just installs a new copy to
  %PROGRAMFILES% resulting in two copies of Firefox to be in place.
  To address this issue this function will uninstall all copies of
  Firefox under 64-bit Windows if it's detected in %PROGRAMFILES(X86)%
  before installing the latest 64-bit version.

  Firefox 67 changed how profiles are named to avoid reusing the same
  profile between different channels of Firefox (std, beta, ESR, etc).
  However the logic used when upgrading from versions before 67 to
  current isn't ideal.  It can, but doesn't always?, create a new
  profile and set it as default; even if there's an existing profile
  being used.  To address this profiles.ini is read to compare with the
  post-install/upgrade state.  If the default is changed to a new
  profile then it is reverted so the original existing profile instead.
  """
  current_default_profile = None
  firefox_exe = f'{os.environ["PROGRAMFILES"]}/Mozilla Firefox/firefox.exe'
  profiles_ini = case_insensitive_path(
    f'{os.environ["APPDATA"]}/Mozilla/Firefox/profiles.ini',
    )
  program_path_32bit_exists = False
  try:
    case_insensitive_path(
      f'{PROGRAMFILES_32}/Mozilla Firefox/firefox.exe',
      )
  except FileNotFoundError:
    # Ignore
    pass
  else:
    program_path_32bit_exists = True
  revert_default = False

  # Save current default profile
  if profiles_ini.exists():
    current_default_profile = get_firefox_default_profile(profiles_ini)

  # Uninstall Firefox if needed
  if ARCH == '64' and program_path_32bit_exists:
    uninstall_firefox()

  # Install Firefox
  run_tool('Firefox', 'Firefox', '/S', download=True)

  # Open Firefox to force profiles.ini update
  popen_program(firefox_exe)
  sleep(5)
  kill_procs('firefox.exe', force=True)

  # Check if default profile changed
  if current_default_profile:
    new_default = get_firefox_default_profile(profiles_ini)
    revert_default = new_default and new_default != current_default_profile

  # Revert default profile if needed
  if revert_default:
    out = []
    for line in profiles_ini.read_text(encoding='utf-8').splitlines():
      if 'Default=Profile' in line:
        out.append(f'Default={current_default_profile}')
      else:
        out.append(line)
    profiles_ini.write_text('\n'.join(out), encoding='utf-8')


def install_libreoffice(
    register_mso_types=True, use_mso_formats=False, vcredist=True):
  """Install LibreOffice."""
  installer = find_kit_dir('Installers').joinpath('LibreOffice.msi')
  xcu_dir = get_path_obj(f'{os.environ.get("APPDATA")}/LibreOffice/4/user')
  xcu_file = xcu_dir.joinpath('registrymodifications.xcu')

  # Set default save formats to MSO types
  if use_mso_formats and not xcu_file.exists():
    xcu_dir.mkdir(parents=True, exist_ok=True)
    with open(xcu_file, 'w', encoding='utf-8', newline='\n') as _f:
      _f.write(LIBREOFFICE_XCU_DATA)

  # Build cmd
  cmd = [
    'msiexec', '/passive', '/norestart',
    '/i', installer,
    'REBOOTYESNO=No',
    f'VC_REDIST={1 if vcredist else 0}',
    ]
  if register_mso_types:
    cmd.append('REGISTER_ALL_MSO_TYPES=1')
  else:
    cmd.append('REGISTER_NO_MSO_TYPES=1')

  # Install LibreOffice
  run_program(cmd)


def install_open_shell():
  """Install Open Shell (just the Start Menu)."""
  installer = get_tool_path('OpenShell', 'OpenShell', check=False)

  # Bail early
  if OS_VERSION != 10:
    raise GenericWarning('Unsupported OS')

  # Install OpenShell
  download_tool('OpenShell', 'OpenShell')
  download_tool('OpenShell', 'Fluent-Metro', suffix='zip')
  cmd = [installer, '/qn', 'ADDLOCAL=StartMenu']
  run_program(cmd)

  # Install Skin
  skin_zip = installer.with_name('Fluent-Metro.zip')
  extract_archive(skin_zip, f'{PROGRAMFILES_64}/Open-Shell/Skins', '-aoa')

  # Add scheduled task to handle OS upgrades
  cmd = ['schtasks', '/query', '/tn', 'Open-Shell OS upgrade check']
  proc = run_program(cmd, check=False)
  if proc.returncode == 0:
    # Task already exists, bail and leave current task unmodified
    return
  cmd = [
    'schtasks', '/create',
    '/ru', r'NT AUTHORITY\SYSTEM',
    '/sc', 'ONSTART',
    '/tn', 'Open-Shell OS upgrade check',
    '/tr', r'"%PROGRAMFILES%\Open-Shell\StartMenu.exe" -upgrade -silent',
    ]
  run_program(cmd)


def install_software_bundle():
  """Install standard software bundle."""
  download_tool('Ninite', 'Software Bundle')
  installer = get_tool_path('Ninite', 'Software Bundle')
  msg = 'Waiting for installations to finish...'
  warning = 'NOTE: Press CTRL+c to manually resume if it gets stuck...'

  # Start installations and wait for them to finish
  print_standard(msg)
  print_warning(warning, end='', flush=True)
  proc = popen_program([installer])
  try:
    proc.wait()
  except KeyboardInterrupt:
    # Assuming user-forced continue
    pass

  # Clear info lines
  print(
    '\r\033[0K'      # Cursor to start of current line and clear to end of line
    '\033[F\033[54C' # Cursor to start of prev line and then move 54 right
    '\033[0K',       # Clear from cursor to end of line
    end='', flush=True)


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


def uninstall_firefox():
  """Uninstall all copies of Firefox."""
  json_file = format_log_path(log_name='Installed Programs', timestamp=True)
  json_file = json_file.with_name(f'{json_file.stem}.json')
  uninstall_data = None

  # Get uninstall_data from UninstallView
  extract_tool('UninstallView')
  cmd = [get_tool_path('UninstallView', 'UninstallView'), '/sjson', json_file]
  run_program(cmd)
  with open(json_file, 'rb') as _f:
    uninstall_data = json.load(_f)

  # Uninstall Firefox if found
  for item in uninstall_data:
    if item['Display Name'].lower().startswith('mozilla firefox'):
      uninstaller = item['Uninstall String'].replace('"', '')
      run_program([uninstaller, '/S'])


# Misc Functions
def get_firefox_default_profile(profiles_ini):
  """Get Firefox default profile, returns pathlib.Path or None."""
  default_profile = None
  parser = None

  # Bail early
  if not profiles_ini.exists():
    return None

  # Parse INI
  parser = configparser.ConfigParser()
  parser.read(profiles_ini)
  for section in parser.sections():
    if section.lower().startswith('install'):
      default_profile = parser[section].get('default')
      break
    value = parser[section].get('default')
    if value and value == '1':
      default_profile = parser[section].get('path')

  # Done
  return default_profile


# Tool Functions
## TODO?

# OS Built-in Functions
## TODO?

if __name__ == '__main__':
  print("This file is not meant to be called directly.")
