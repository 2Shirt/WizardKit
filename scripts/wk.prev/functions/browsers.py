# Wizard Kit: Functions - Browsers

from functions.common import *
from operator import itemgetter
from settings.browsers import *


# Define other_results for later try_and_print
browser_data = {}
other_results = {
  'Error': {
    'MultipleInstallationsError': 'Multiple installations detected',
    },
  'Warning': {
    'NotInstalledError': 'Not installed',
    'NoProfilesError': 'No profiles found',
    }
  }


def archive_all_users():
  """Create backups for all browsers for all users."""
  users_root = r'{}\Users'.format(global_vars['Env']['SYSTEMDRIVE'])
  user_envs = []

  # Build list of valid users
  for user_name in os.listdir(users_root):
    valid_user = True
    if user_name in ('Default', 'Default User'):
      # Skip default users
      continue
    user_path = os.path.join(users_root, user_name)
    appdata_local = os.path.join(user_path, r'AppData\Local')
    appdata_roaming = os.path.join(user_path, r'AppData\Roaming')
    valid_user = valid_user and os.path.exists(appdata_local)
    valid_user = valid_user and os.path.exists(appdata_roaming)
    if valid_user:
      user_envs.append({
        'USERNAME': user_name,
        'USERPROFILE': user_path,
        'APPDATA': appdata_roaming,
        'LOCALAPPDATA': appdata_local})

  # Backup browsers for all valid users
  print_info('Backing up browsers')
  for fake_env in sorted(user_envs, key=itemgetter('USERPROFILE')):
    print_standard('  {}'.format(fake_env['USERNAME']))
    for b_k, b_v in sorted(SUPPORTED_BROWSERS.items()):
      if b_k == 'Mozilla Firefox Dev':
        continue
      source_path = b_v['user_data_path'].format(**fake_env)
      if not os.path.exists(source_path):
        continue
      source_items = source_path + '*'
      archive_path = r'{BackupDir}\Browsers ({USERNAME})\{Date}'.format(
        **global_vars, **fake_env)
      os.makedirs(archive_path, exist_ok=True)
      archive_path += r'\{}.7z'.format(b_k)
      cmd = [
        global_vars['Tools']['SevenZip'],
        'a', '-aoa', '-bso0', '-bse0', '-mx=1',
        archive_path, source_items]
      try_and_print(message='{}...'.format(b_k),
        function=run_program, cmd=cmd)
    print_standard(' ')


def archive_browser(name):
  """Create backup of Browser saved in the BackupDir."""
  source = '{}*'.format(browser_data[name]['user_data_path'])
  dest = r'{BackupDir}\Browsers ({USERNAME})\{Date}'.format(
    **global_vars, **global_vars['Env'])
  archive = r'{}\{}.7z'.format(dest, name)
  os.makedirs(dest, exist_ok=True)
  cmd = [
    global_vars['Tools']['SevenZip'],
    'a', '-aoa', '-bso0', '-bse0', '-mx=1',
    '-mhe=on', '-p{}'.format(ARCHIVE_PASSWORD),
    archive, source]
  run_program(cmd)


def backup_browsers():
  """Create backup of all detected browser profiles."""
  for name in [k for k, v in sorted(browser_data.items()) if v['profiles']]:
    try_and_print(message='{}...'.format(name),
    function=archive_browser, name=name)


def clean_chromium_profile(profile):
  """Recreate profile with only the essential user data.

  This is done by renaming the existing profile, creating a new folder
  with the original name, then copying the essential files from the
  backup folder. This way the original state is preserved in case
  something goes wrong.
  """
  if profile is None:
    raise Exception
  backup_path = '{path}_{Date}.bak'.format(
    path=profile['path'], **global_vars)
  backup_path = non_clobber_rename(backup_path)
  shutil.move(profile['path'], backup_path)
  os.makedirs(profile['path'], exist_ok=True)

  # Restore essential files from backup_path
  for entry in os.scandir(backup_path):
    if REGEX_CHROMIUM_ITEMS.search(entry.name):
      shutil.copy(entry.path, r'{}\{}'.format(
        profile['path'], entry.name))


def clean_internet_explorer(**kwargs):
  """Uses the built-in function to reset IE and sets the homepage.

  NOTE: kwargs set but unused as a workaround."""
  kill_process('iexplore.exe')
  run_program(['rundll32.exe', 'inetcpl.cpl,ResetIEtoDefaults'], check=False)
  key = r'Software\Microsoft\Internet Explorer\Main'

  # Set homepage
  with winreg.OpenKey(HKCU, key, access=winreg.KEY_WRITE) as _key:
    winreg.SetValueEx(_key, 'Start Page', 0,
      winreg.REG_SZ, DEFAULT_HOMEPAGE)
    try:
      winreg.DeleteValue(_key, 'Secondary Start Pages')
    except FileNotFoundError:
      pass


def clean_mozilla_profile(profile):
  """Recreate profile with only the essential user data.

  This is done by renaming the existing profile, creating a new folder
  with the original name, then copying the essential files from the
  backup folder. This way the original state is preserved in case
  something goes wrong.
  """
  if profile is None:
    raise Exception
  backup_path = '{path}_{Date}.bak'.format(
    path=profile['path'], **global_vars)
  backup_path = non_clobber_rename(backup_path)
  shutil.move(profile['path'], backup_path)
  homepages = []
  os.makedirs(profile['path'], exist_ok=True)

  # Restore essential files from backup_path
  for entry in os.scandir(backup_path):
    if REGEX_MOZILLA.search(entry.name):
      if entry.is_dir():
        shutil.copytree(entry.path, r'{}\{}'.format(
          profile['path'], entry.name))
      else:
        shutil.copy(entry.path, r'{}\{}'.format(
          profile['path'], entry.name))

  # Set profile defaults
  with open(r'{path}\prefs.js'.format(**profile), 'a', encoding='ascii') as f:
    for k, v in MOZILLA_PREFS.items():
      f.write('user_pref("{}", {});\n'.format(k, v))


def get_browser_details(name):
  """Get installation and profile details for all supported browsers."""
  browser = SUPPORTED_BROWSERS[name].copy()

  # Update user_data_path
  browser['user_data_path'] = browser['user_data_path'].format(
    **global_vars['Env'])

  # Find executable (if multiple files are found, the last one is used)
  exe_path = None
  num_installs = 0
  for install_path in ['LOCALAPPDATA', 'PROGRAMFILES(X86)', 'PROGRAMFILES']:
    test_path = r'{install_path}\{rel_install_path}\{exe_name}'.format(
      install_path = global_vars['Env'].get(install_path, ''),
      **browser)
    if os.path.exists(test_path):
      num_installs += 1
      exe_path = test_path

  # Find profile(s)
  profiles = []
  if browser['base'] == 'ie':
    profiles.append({'name': 'Default', 'path': None})
  elif 'Google Chrome' in name:
    profiles.extend(
      get_chromium_profiles(
        search_path=browser['user_data_path']))
  elif browser['base'] == 'mozilla':
    dev = 'Dev' in name
    profiles.extend(
      get_mozilla_profiles(
        search_path=browser['user_data_path'], dev=dev))
    if exe_path and not dev and len(profiles) == 0:
      # e.g. If Firefox is installed but no profiles were found.
      ## Rename profiles.ini and create a new default profile
      profiles_ini_path = browser['user_data_path'].replace(
        'Profiles', 'profiles.ini')
      if os.path.exists(profiles_ini_path):
        backup_path = '{path}_{Date}.bak'.format(
          path=profiles_ini_path, **global_vars)
        backup_path = non_clobber_rename(backup_path)
        shutil.move(profiles_ini_path, backup_path)
      run_program([exe_path, '-createprofile', 'default'], check=False)
      profiles.extend(
        get_mozilla_profiles(
          search_path=browser['user_data_path'], dev=dev))

  elif 'Opera' in name:
    if os.path.exists(browser['user_data_path']):
      profiles.append(
        {'name': 'Default', 'path': browser['user_data_path']})

  # Get homepages
  if browser['base'] == 'ie':
    # IE is set to only have one profile above
    profiles[0]['homepages'] = get_ie_homepages()
  elif browser['base'] == 'mozilla':
    for profile in profiles:
      prefs_path = r'{path}\prefs.js'.format(**profile)
      profile['homepages'] = get_mozilla_homepages(prefs_path=prefs_path)

  # Add to browser_data
  browser_data[name] = browser
  browser_data[name].update({
    'exe_path': exe_path,
    'profiles': profiles,
    })

  # Raise installation warnings (if any)
  if num_installs == 0:
    raise NotInstalledError
  elif num_installs > 1 and browser['base'] != 'ie':
    raise MultipleInstallationsError


def get_chromium_profiles(search_path):
  """Find any chromium-style profiles and return as a list of dicts."""
  profiles = []
  try:
    for entry in os.scandir(search_path):
      if entry.is_dir() and REGEX_CHROMIUM_PROFILE.search(entry.name):
        profiles.append(entry)
        REGEX_PROFILE_BACKUP = r'\.\w+bak.*'
    profiles = [p for p in profiles if not REGEX_BACKUP.search(p.name)]
    # Convert os.DirEntries to dicts
    profiles = [{'name': p.name, 'path': p.path} for p in profiles]
  except Exception:
    pass

  return profiles


def get_ie_homepages():
  """Read homepages from the registry and return as a list."""
  homepages = []
  main_page = ''
  extra_pages = []
  key = r'Software\Microsoft\Internet Explorer\Main'
  with winreg.OpenKey(HKCU, key) as _key:
     try:
       main_page = winreg.QueryValueEx(_key, 'Start Page')[0]
     except FileNotFoundError:
       pass
     try:
       extra_pages = winreg.QueryValueEx(_key, 'Secondary Start Pages')[0]
     except FileNotFoundError:
       pass
  if main_page != '':
    homepages.append(main_page)
  if len(extra_pages) > 0:
    homepages.extend(extra_pages)

  # Remove all curly braces
  homepages = [h.replace('{', '').replace('}', '') for h in homepages]
  return homepages


def get_mozilla_homepages(prefs_path):
  """Read homepages from prefs.js and return as a list."""
  homepages = []
  try:
    with open(prefs_path, 'r') as f:
      search = re.search(
        r'browser\.startup\.homepage", "([^"]*)"',
        f.read(), re.IGNORECASE)
      if search:
        homepages = search.group(1).split('|')
  except Exception:
    pass

  return homepages


def get_mozilla_profiles(search_path, dev=False):
  """Find any mozilla-style profiles and return as a list of dicts."""
  profiles = []
  try:
    for entry in os.scandir(search_path):
      if entry.is_dir():
        if 'dev-edition' in entry.name:
          # NOTE: Not always present which can lead
          # to Dev profiles being marked as non-Dev
          ## NOTE 2: It is possible that a non-Dev profile
          ##    to be created with 'dev-edition' in the name.
          ##    (It wouldn't make sense, but possible)
          if dev:
            profiles.append(entry)
        elif not dev:
          profiles.append(entry)
    profiles = [p for p in profiles if not REGEX_BACKUP.search(p.name)]
    # Convert os.DirEntries to dicts
    profiles = [{'name': p.name, 'path': p.path} for p in profiles]
  except Exception:
    pass

  return profiles


def install_adblock(indent=8, width=32, just_firefox=False):
  """Install adblock for all supported browsers."""
  for browser in sorted(browser_data):
    if just_firefox and browser_data[browser]['base'] != 'mozilla':
      continue
    exe_path = browser_data[browser].get('exe_path', None)
    if not exe_path:
      if browser_data[browser]['profiles']:
        print_standard(
          '{indent}{browser:<{width}}'.format(
            indent=' '*indent, width=width, browser=browser+'...'),
          end='', flush=True)
        print_warning('Profile(s) detected but browser not installed',
          timestamp=False)
      else:
        # Only warn if profile(s) are detected.
        pass
    else:
      # Set urls to open
      urls = []
      if browser_data[browser]['base'] == 'chromium':
        if browser == 'Google Chrome':
          # Check for system exensions
          try:
            winreg.QueryValue(HKLM, UBO_CHROME_REG)
          except FileNotFoundError:
            urls.append(UBO_CHROME)
          try:
            winreg.QueryValue(HKLM, UBO_EXTRA_CHROME_REG)
          except FileNotFoundError:
            urls.append(UBO_EXTRA_CHROME)

          if len(urls) == 0:
            urls = ['chrome://extensions']
        elif 'Opera' in browser:
          urls.append(UBO_OPERA)
        else:
          urls.append(UBO_CHROME)
          urls.append(UBO_EXTRA_CHROME)

      elif browser_data[browser]['base'] == 'mozilla':
        # Check for system extensions
        try:
          with winreg.OpenKey(HKLM, UBO_MOZILLA_REG) as key:
            winreg.QueryValueEx(key, UBO_MOZILLA_REG_NAME)
        except FileNotFoundError:
          urls = [UBO_MOZILLA]
        else:
          if os.path.exists(UBO_MOZZILA_PATH):
            urls = ['about:addons']
          else:
            urls = [UBO_MOZILLA]

      elif browser_data[browser]['base'] == 'ie':
        urls.append(IE_GALLERY)

      # By using check=False we're skipping any return codes so
      # it should only fail if the program can't be run
      #   (or can't be found).
      # In other words, this isn't tracking the addon/extension's
      #   installation status.
      try_and_print(message='{}...'.format(browser),
        indent=indent, width=width,
        cs='Started', function=popen_program,
        cmd=[exe_path, *urls], check=False)


def is_installed(browser_name):
  """Checks if browser is installed based on exe_path, returns bool."""
  browser_name = browser_name.replace(' Chromium', '')
  return bool(browser_data.get(browser_name, {}).get('exe_path', False))


def list_homepages(indent=8, width=32):
  """List current homepages for reference."""
  browser_list = [k for k, v in sorted(browser_data.items()) if v['exe_path']]
  for browser in browser_list:
    # Skip Chromium-based browsers
    if browser_data[browser]['base'] == 'chromium':
      print_info(
        '{indent}{browser:<{width}}'.format(
          indent=' '*indent, width=width, browser=browser+'...'),
        end='', flush=True)
      print_warning('Not implemented', timestamp=False)
      continue

    # All other browsers
    print_info('{indent}{browser:<{width}}'.format(
      indent=' '*indent, width=width, browser=browser+'...'))
    for profile in browser_data[browser].get('profiles', []):
      name = profile.get('name', '?')
      homepages = profile.get('homepages', [])
      if len(homepages) == 0:
        print_standard(
          '{indent}{name:<{width}}'.format(
            indent=' '*indent, width=width, name=name),
          end='', flush=True)
        print_warning('None found', timestamp=False)
      else:
        for page in homepages:
          print_standard('{indent}{name:<{width}}{page}'.format(
            indent=' '*indent, width=width, name=name, page=page))


def profile_present(browser_name):
  """Checks if a profile was detected for browser, returns bool."""
  browser_name = browser_name.replace(' Chromium', '')
  return bool(browser_data.get(browser_name, {}).get('profiles', False))


def reset_browsers(indent=8, width=32):
  """Reset all detected browsers to safe defaults."""
  browser_list = [k for k, v in sorted(browser_data.items()) if v['profiles']]
  for browser in browser_list:
    print_info('{indent}{name}'.format(indent=' '*indent, name=browser))
    for profile in browser_data[browser]['profiles']:
      if browser_data[browser]['base'] == 'chromium':
        function = clean_chromium_profile
      elif browser_data[browser]['base'] == 'ie':
        function = clean_internet_explorer
      elif browser_data[browser]['base'] == 'mozilla':
        function = clean_mozilla_profile
      try_and_print(
        message='{}...'.format(profile['name']),
        indent=indent, width=width, function=function,
        other_results=other_results, profile=profile)


def scan_for_browsers(just_firefox=False, silent=False):
  """Scan system for any supported browsers."""
  for name, details in sorted(SUPPORTED_BROWSERS.items()):
    if just_firefox and details['base'] != 'mozilla':
      continue
    if silent:
      try:
        get_browser_details(name)
      except Exception:
        # Ignore errors in silent mode
        pass
    else:
      try_and_print(message='{}...'.format(name),
        function=get_browser_details, cs='Detected',
        other_results=other_results, name=name)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
