# Wizard Kit: Functions - Setup

from functions.browsers import *
from functions.json import *
from functions.update import *
from settings.setup import *
from settings.sources import *


# Configuration
def config_classicstart():
  """Configure ClassicStart."""
  # User level, not system level
  cs_exe = r'{PROGRAMFILES}\Classic Shell\ClassicStartMenu.exe'.format(
    **global_vars['Env'])
  skin = r'{PROGRAMFILES}\Classic Shell\Skins\Metro-Win10-Black.skin7'.format(
    **global_vars['Env'])
  extract_item('ClassicStartSkin', silent=True)

  # Stop Classic Start
  run_program([cs_exe, '-exit'], check=False)
  sleep(1)
  kill_process('ClassicStartMenu.exe')

  # Configure
  write_registry_settings(SETTINGS_CLASSIC_START, all_users=False)
  if global_vars['OS']['Version'] == '10' and os.path.exists(skin):
    # Enable Win10 theme if on Win10
    key_path = r'Software\IvoSoft\ClassicStartMenu\Settings'
    with winreg.OpenKey(HKCU, key_path, access=winreg.KEY_WRITE) as key:
      winreg.SetValueEx(
        key, 'SkinW7', 0, winreg.REG_SZ, 'Metro-Win10-Black')
      winreg.SetValueEx(key, 'SkinVariationW7', 0, winreg.REG_SZ, '')

  # Pin Browser to Start Menu (Classic)
  firefox = r'{PROGRAMDATA}\Start Menu\Programs\Mozilla Firefox.lnk'.format(
    **global_vars['Env'])
  chrome = r'{PROGRAMDATA}\Start Menu\Programs\Google Chrome.lnk'.format(
    **global_vars['Env'])
  dest_path = r'{APPDATA}\ClassicShell\Pinned'.format(**global_vars['Env'])
  source = None
  dest = None
  if os.path.exists(firefox):
    source = firefox
    dest = r'{}\Mozilla Firefox.lnk'.format(dest_path)
  elif os.path.exists(chrome):
    source = chrome
    dest = r'{}\Google Chrome.lnk'.format(dest_path)
  if source:
    try:
      os.makedirs(dest_path, exist_ok=True)
      shutil.copy(source, dest)
    except Exception:
      pass # Meh, it's fine without

  # (Re)start Classic Start
  run_program([cs_exe, '-exit'], check=False)
  sleep(1)
  kill_process('ClassicStartMenu.exe')
  sleep(1)
  popen_program(cs_exe)


def config_explorer_system():
  """Configure Windows Explorer for all users."""
  write_registry_settings(SETTINGS_EXPLORER_SYSTEM, all_users=True)


def config_explorer_user(setup_mode='All'):
  """Configure Windows Explorer for current user per setup_mode."""
  settings_explorer_user = {
    k: v for k, v in SETTINGS_EXPLORER_USER.items()
    if setup_mode not in v.get('Invalid modes', [])
    }
  write_registry_settings(settings_explorer_user, all_users=False)


def config_windows_updates():
  """Configure Windows updates."""
  write_registry_settings(SETTINGS_WINDOWS_UPDATES, all_users=True)


def update_clock():
  """Set Timezone and sync clock."""
  run_program(['tzutil', '/s', WINDOWS_TIME_ZONE], check=False)
  run_program(['net', 'stop', 'w32ime'], check=False)
  run_program(
    ['w32tm', '/config', '/syncfromflags:manual',
      '/manualpeerlist:"us.pool.ntp.org time.nist.gov time.windows.com"',
      ],
    check=False)
  run_program(['net', 'start', 'w32ime'], check=False)
  run_program(['w32tm', '/resync', '/nowait'], check=False)


def write_registry_settings(settings, all_users=False):
  """Write registry values from custom dict of dicts."""
  hive = HKCU
  if all_users:
    hive = HKLM
  for k, v in settings.items():
    # CreateKey
    access = winreg.KEY_WRITE
    if 'WOW64_32' in v:
      access = access | winreg.KEY_WOW64_32KEY
    winreg.CreateKeyEx(hive, k, 0, access)

    # Create values
    with winreg.OpenKeyEx(hive, k, 0, access) as key:
      for name, value in v.get('DWORD Items', {}).items():
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
      for name, value in v.get('SZ Items', {}).items():
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


# Installations
def find_current_software():
  """Find currently installed software, returns list."""
  ninite_extras_path = r'{BaseDir}\Installers\Extras'.format(**global_vars)
  installers = []

  # Browsers
  scan_for_browsers(silent=True)
  for browser in ('Google Chrome', 'Mozilla Firefox', 'Opera Chromium'):
    if is_installed(browser):
      installers.append(
        r'{}\Web Browsers\{}.exe'.format(ninite_extras_path, browser))

  # TODO: Add more sections

  return installers

def find_missing_software():
  """Find missing software based on dirs/files present, returns list."""
  ninite_extras_path = r'{BaseDir}\Installers\Extras'.format(**global_vars)
  installers = []

  # Browsers
  scan_for_browsers(silent=True)
  for browser in ('Google Chrome', 'Mozilla Firefox', 'Opera Chromium'):
    if profile_present(browser):
      installers.append(
        r'{}\Web Browsers\{}.exe'.format(ninite_extras_path, browser))

  # TODO: Add more sections

  return installers


def install_adobe_reader():
  """Install Adobe Reader."""
  cmd = [
    r'{BaseDir}\Installers\Extras\Office\Adobe Reader DC.exe'.format(
      **global_vars),
    '/sAll',
    '/msi', '/norestart', '/quiet',
    'ALLUSERS=1',
    'EULA_ACCEPT=YES']
  run_program(cmd)


def install_chrome_extensions():
  """Install Google Chrome extensions for all users."""
  write_registry_settings(SETTINGS_GOOGLE_CHROME, all_users=True)


def install_classicstart_skin():
  """Extract ClassicStart skin to installation folder."""
  if global_vars['OS']['Version'] not in ('8', '8.1', '10'):
    raise UnsupportedOSError
  extract_item('ClassicStartSkin', silent=True)
  source = r'{BinDir}\ClassicStartSkin\Metro-Win10-Black.skin7'.format(
    **global_vars)
  dest_path = r'{PROGRAMFILES}\Classic Shell\Skins'.format(
    **global_vars['Env'])
  dest = r'{}\Metro-Win10-Black.skin7'.format(dest_path)
  os.makedirs(dest_path, exist_ok=True)
  shutil.copy(source, dest)


def install_firefox_extensions():
  """Install Firefox extensions for all users."""
  dist_path = r'{PROGRAMFILES}\Mozilla Firefox\distribution\extensions'.format(
    **global_vars['Env'])
  source_path = r'{CBinDir}\FirefoxExtensions.7z'.format(**global_vars)
  if not os.path.exists(source_path):
    raise FileNotFoundError

  # Update registry
  write_registry_settings(SETTINGS_MOZILLA_FIREFOX_32, all_users=True)
  write_registry_settings(SETTINGS_MOZILLA_FIREFOX_64, all_users=True)

  # Extract extension(s) to distribution folder
  cmd = [
    global_vars['Tools']['SevenZip'], 'e', '-aos', '-bso0', '-bse0',
    '-p{ArchivePassword}'.format(**global_vars),
    '-o{dist_path}'.format(dist_path=dist_path),
    source_path]
  run_program(cmd)


def install_libreoffice(
    quickstart=True, register_mso_types=True,
    use_mso_formats=False, vcredist=False):
  """Install LibreOffice using specified settings."""
  cmd = [
    'msiexec', '/passive', '/norestart',
    '/i', r'{}\Installers\Extras\Office\LibreOffice.msi'.format(
      global_vars['BaseDir']),
    'REBOOTYESNO=No',
    'ISCHECKFORPRODUCTUPDATES=0',
    'QUICKSTART={}'.format(1 if quickstart else 0),
    'UI_LANGS=en_US',
    'VC_REDIST={}'.format(1 if vcredist else 0),
    ]
  if register_mso_types:
    cmd.append('REGISTER_ALL_MSO_TYPES=1')
  else:
    cmd.append('REGISTER_NO_MSO_TYPES=1')
  xcu_dir = r'{APPDATA}\LibreOffice\4\user'.format(**global_vars['Env'])
  xcu_file = r'{}\registrymodifications.xcu'.format(xcu_dir)

  # Set default save format
  if use_mso_formats and not os.path.exists(xcu_file):
    os.makedirs(xcu_dir, exist_ok=True)
    with open(xcu_file, 'w', encoding='utf-8', newline='\n') as f:
      f.write(LIBREOFFICE_XCU_DATA)

  # Install LibreOffice
  run_program(cmd, check=True)

def install_ninite_bundle(
    # pylint: disable=too-many-arguments,too-many-branches
    base=True,
    browsers_only=False,
    libreoffice=False,
    missing=False,
    mse=False,
    standard=True,
    ):
  """Run Ninite installer(s), returns list of Popen objects."""
  popen_objects = []
  if browsers_only:
    # This option is deprecated
    installer_path = r'{BaseDir}\Installers\Extras\Web Browsers'.format(
      **global_vars)
    scan_for_browsers(silent=True)
    for browser in ('Google Chrome', 'Mozilla Firefox', 'Opera Chromium'):
      if is_installed(browser):
        cmd = r'{}\{}.exe'.format(installer_path, browser)
        popen_objects.append(popen_program(cmd))

    # Bail
    return popen_objects

  # Main selections
  main_selections = []
  if base:
    main_selections.append('base')
  if standard:
    if global_vars['OS']['Version'] in ('8', '8.1', '10'):
      main_selections.append('standard')
    else:
      main_selections.append('standard7')
  if main_selections:
    # Only run if base and/or standard are enabled
    cmd = r'{}\Installers\Extras\Bundles\{}.exe'.format(
      global_vars['BaseDir'],
      '-'.join(main_selections),
      )
    popen_objects.append(popen_program([cmd]))

  # Extra selections
  extra_selections = {}
  for cmd in find_current_software():
    extra_selections[cmd] = True
  if missing:
    for cmd in find_missing_software():
      extra_selections[cmd] = True

  # Remove overlapping selections
  regex = []
  for n_name, n_group in NINITE_REGEX.items():
    if n_name in main_selections:
      regex.extend(n_group)
  regex = '({})'.format('|'.join(regex))
  extra_selections = {
    cmd: True for cmd in extra_selections
    if not re.search(regex, cmd, re.IGNORECASE)
    }

  # Start extra selections
  for cmd in extra_selections:
    popen_objects.append(popen_program([cmd]))

  # Microsoft Security Essentials
  if mse:
    cmd = r'{}\Installers\Extras\Security\{}'.format(
      global_vars['BaseDir'],
      'Microsoft Security Essentials.exe',
      )
    popen_objects.append(popen_program([cmd]))

  # LibreOffice
  if libreoffice:
    cmd = r'{}\Installers\Extras\Office\{}'.format(
      global_vars['BaseDir'],
      'LibreOffice.exe',
      )
    popen_objects.append(popen_program([cmd]))

  # Done
  return popen_objects


def install_vcredists():
  """Install all supported Visual C++ runtimes."""
  extract_item('_vcredists', silent=True)
  prev_dir = os.getcwd()
  try:
    os.chdir(r'{BinDir}\_vcredists'.format(**global_vars))
  except FileNotFoundError:
    # Ignored since the loop below will report the errors
    pass
  for vcr in VCR_REDISTS:
    try_and_print(message=vcr['Name'], function=run_program,
      cmd=vcr['Cmd'], other_results=OTHER_RESULTS)

  os.chdir(prev_dir)


# Misc
def open_device_manager():
  popen_program(['mmc', 'devmgmt.msc'])


def open_windows_activation():
  popen_program(['slui'])


def open_windows_updates():
  popen_program(['control', '/name', 'Microsoft.WindowsUpdate'])


def restart_explorer():
  """Restart Explorer."""
  kill_process('explorer.exe')
  sleep(2)
  kill_process('explorer.exe')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
