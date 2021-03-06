# Wizard Kit: Functions - Information

from borrowed import knownpaths
from functions.activation import *
from operator import itemgetter
from settings.info import *


def backup_file_list():
  """Export current file listing for the system."""
  extract_item('Everything', silent=True)
  cmd = [
    global_vars['Tools']['Everything'],
    '-nodb',
    '-create-filelist',
    r'{LogDir}\File List.txt'.format(**global_vars),
    global_vars['Env']['SYSTEMDRIVE']]
  run_program(cmd)


def backup_power_plans():
  """Export current power plans."""
  os.makedirs(r'{BackupDir}\Power Plans\{Date}'.format(
    **global_vars), exist_ok=True)
  plans = run_program(['powercfg', '/L'])
  plans = plans.stdout.decode().splitlines()
  plans = [p for p in plans if re.search(r'^Power Scheme', p)]
  for p in plans:
    guid = re.sub(r'Power Scheme GUID:\s+([0-9a-f\-]+).*', r'\1', p)
    name = re.sub(
      r'Power Scheme GUID:\s+[0-9a-f\-]+\s+\(([^\)]+)\).*', r'\1', p)
    out = r'{BackupDir}\Power Plans\{Date}\{name}.pow'.format(
      name=name, **global_vars)
    if not os.path.exists(out):
      cmd = ['powercfg', '-export', out, guid]
      run_program(cmd, check=False)


def backup_registry(overwrite=False):
  """Backup registry including user hives."""
  extract_item('erunt', silent=True)
  cmd = [
    global_vars['Tools']['ERUNT'],
    r'{BackupDir}\Registry\{Date}'.format(**global_vars),
    'sysreg',
    'curuser',
    'otherusers',
    '/noprogresswindow']
  if overwrite:
    cmd.append('/noconfirmdelete')
  run_program(cmd)


def get_folder_size(path):
  """Get (human-readable) size of folder passed, returns str."""
  size = 'Unknown'
  cmd = [global_vars['Tools']['Du'], '-c', '-nobanner', '-q', path]
  try:
    out = run_program(cmd)
  except FileNotFoundError:
    # Failed to find folder
    pass
  except subprocess.CalledProcessError:
    # Failed to get folder size
    pass
  else:
    try:
      size = out.stdout.decode().split(',')[-2]
    except IndexError:
      # Failed to parse csv data
      pass
    else:
      size = human_readable_size(size)
  return size


def get_installed_antivirus():
  """Get list of installed Antivirus programs."""
  programs = []
  cmd = ['WMIC', r'/namespace:\\root\SecurityCenter2',
    'path', 'AntivirusProduct',
    'get', 'displayName', '/value']
  out = run_program(cmd)
  out = out.stdout.decode().strip()
  products = out.splitlines()
  products = [p.split('=')[1] for p in products if p]
  for prod in sorted(products):
    # Get product state and check if it's enabled
    # credit: https://jdhitsolutions.com/blog/powershell/5187/get-antivirus-product-status-with-powershell/
    cmd = ['WMIC', r'/namespace:\\root\SecurityCenter2',
      'path', 'AntivirusProduct',
      'where', 'displayName="{}"'.format(prod),
      'get', 'productState', '/value']
    out = run_program(cmd)
    out = out.stdout.decode().strip()
    state = out.split('=')[1]
    state = hex(int(state))
    if str(state)[3:5] not in ['10', '11']:
      programs.append('[Disabled] {}'.format(prod))
    else:
      programs.append(prod)

  if len(programs) == 0:
    programs = ['No programs found']
  return programs


def get_installed_office():
  """Get list of installed Office programs."""
  programs = []
  log_file = r'{LogDir}\Installed Program List (AIDA64).txt'.format(
    **global_vars)
  with open (log_file, 'r') as f:
    for line in sorted(f.readlines()):
      if REGEX_OFFICE.search(line):
        programs.append(line[4:82].strip())

  if len(programs) == 0:
    programs = ['No programs found']
  return programs


def get_shell_path(folder, user='current'):
  """Get shell path using knownpaths, returns str.

  NOTE: Only works for the current user.
  Code based on https://gist.github.com/mkropat/7550097
  """
  path = None
  folderid = None
  if user.lower() == 'public':
    user = 'common'
  try:
    folderid = getattr(knownpaths.FOLDERID, folder)
  except AttributeError:
    # Unknown folder ID, ignore and return None
    pass

  if folderid:
    try:
      path = knownpaths.get_path(
        folderid, getattr(knownpaths.UserHandle, user))
    except PathNotFoundError:
      # Folder not found, ignore and return None
      pass

  return path


def get_user_data_paths(user):
  """Get user data paths for provided user, returns dict."""
  hive_path = user['SID']
  paths = {
    'Profile': {
      'Path': None,
      },
    'Shell Folders': {},
    'Extra Folders': {},
    }
  unload_hive = False

  if user['Name'] == global_vars['Env']['USERNAME']:
    # We can use SHGetKnownFolderPath for the current user
    paths['Profile']['Path'] = get_shell_path('Profile')
    paths['Shell Folders'] = {f: {'Path': get_shell_path(f)}
      for f in SHELL_FOLDERS.keys()}
  else:
    # We have to use the NTUSER.dat hives which isn't recommended by MS
    try:
      key_path = r'{}\{}'.format(REG_PROFILE_LIST, user['SID'])
      with winreg.OpenKey(HKLM, key_path) as key:
        paths['Profile']['Path'] = winreg.QueryValueEx(
          key, 'ProfileImagePath')[0]
    except Exception:
      # Profile path not found, leaving as None.
      pass

    # Shell folders (Prep)
    if not reg_path_exists(HKU, hive_path) and paths['Profile']['Path']:
      # User not logged-in, loading hive
      # Also setting unload_hive so it will be unloaded later.
      hive_path = TMP_HIVE_PATH
      cmd = ['reg', 'load', r'HKU\{}'.format(TMP_HIVE_PATH),
        r'{}\NTUSER.DAT'.format(paths['Profile']['Path'])]
      unload_hive = True
      try:
        run_program(cmd)
      except subprocess.CalledProcessError:
        # Failed to load user hive
        pass

    # Shell folders
    shell_folders = r'{}\{}'.format(hive_path, REG_SHELL_FOLDERS)
    if (reg_path_exists(HKU, hive_path)
      and reg_path_exists(HKU, shell_folders)):
      with winreg.OpenKey(HKU, shell_folders) as key:
        for folder, values in SHELL_FOLDERS.items():
          for value in values:
            try:
              path = winreg.QueryValueEx(key, value)[0]
            except FileNotFoundError:
              # Skip missing values
              pass
            else:
              paths['Shell Folders'][folder] = {'Path': path}
              # Stop checking values for this folder
              break

    # Shell folder (extra check)
    if paths['Profile']['Path']:
      for folder in SHELL_FOLDERS.keys():
        folder_path = r'{Path}\{folder}'.format(
          folder=folder, **paths['Profile'])
        if (folder not in paths['Shell Folders']
          and os.path.exists(folder_path)):
          paths['Shell Folders'][folder] = {'Path': folder_path}

  # Extra folders
  if paths['Profile']['Path']:
    for folder in EXTRA_FOLDERS:
      folder_path = r'{Path}\{folder}'.format(
        folder=folder, **paths['Profile'])
      if os.path.exists(folder_path):
        paths['Extra Folders'][folder] = {'Path': folder_path}

  # Shell folders (cleanup)
  if unload_hive:
    cmd = ['reg', 'unload', r'HKU\{}'.format(TMP_HIVE_PATH)]
    run_program(cmd, check=False)

  # Done
  return paths


def get_user_folder_sizes(users):
  """Update list(users) to include folder paths and sizes."""
  extract_item('du', filter='du*', silent=True)
  # Configure Du
  winreg.CreateKey(HKCU, r'Software\Sysinternals\Du')
  with winreg.OpenKey(HKCU,
    r'Software\Sysinternals\Du', access=winreg.KEY_WRITE) as key:
    winreg.SetValueEx(key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)

  for u in users:
    u.update(get_user_data_paths(u))
    if u['Profile']['Path']:
      u['Profile']['Size'] = get_folder_size(u['Profile']['Path'])
      for folder in u['Shell Folders'].keys():
        u['Shell Folders'][folder]['Size'] = get_folder_size(
          u['Shell Folders'][folder]['Path'])
      for folder in u['Extra Folders'].keys():
        u['Extra Folders'][folder]['Size'] = get_folder_size(
          u['Extra Folders'][folder]['Path'])


def get_user_list():
  """Get user list via WMIC, returns list of dicts."""
  users = []

  # Get user info from WMI
  cmd = ['wmic', 'useraccount', 'get', '/format:csv']
  try:
    out = run_program(cmd)
  except subprocess.CalledProcessError:
    # Meh, return empty list to avoid a full crash
    return users

  entries = out.stdout.decode().splitlines()
  entries = [e.strip().split(',') for e in entries if e.strip()]

  # Add user(s) to dict
  keys = entries[0]
  for e in entries[1:]:
    # Create dict using 1st line (keys)
    e = dict(zip(keys, e))
    # Set Active status via 'Disabled' TRUE/FALSE str
    e['Active'] = bool(e['Disabled'].upper() == 'FALSE')
    # Assume SIDs ending with 1000+ are "Standard" and others are "System"
    e['Type'] = 'Standard' if re.search(r'-1\d+$', e['SID']) else 'System'
    users.append(e)

  # Sort list
  users.sort(key=itemgetter('Name'))

  # Done
  return users


def reg_path_exists(hive, path):
  """Test if specified path exists, returns bool."""
  try:
    winreg.QueryValue(hive, path)
  except FileNotFoundError:
    return False
  else:
    return True


def run_aida64():
  """Run AIDA64 to save system reports."""
  extract_item('AIDA64', silent=True)
  # All system info
  config = r'{BinDir}\AIDA64\full.rpf'.format(**global_vars)
  report_file = r'{LogDir}\System Information (AIDA64).html'.format(
    **global_vars)
  if not os.path.exists(report_file):
    cmd = [
      global_vars['Tools']['AIDA64'],
      '/R', report_file,
      '/CUSTOM', config,
      '/HTML', '/SILENT', '/SAFEST']
    run_program(cmd, check=False)

  # Installed Programs
  config = r'{BinDir}\AIDA64\installed_programs.rpf'.format(**global_vars)
  report_file = r'{LogDir}\Installed Program List (AIDA64).txt'.format(
    **global_vars)
  if not os.path.exists(report_file):
    cmd = [
      global_vars['Tools']['AIDA64'],
      '/R', report_file,
      '/CUSTOM', config,
      '/TEXT', '/SILENT', '/SAFEST']
    run_program(cmd, check=False)

  # Product Keys
  config = r'{BinDir}\AIDA64\licenses.rpf'.format(**global_vars)
  report_file = r'{LogDir}\Product Keys (AIDA64).txt'.format(**global_vars)
  if not os.path.exists(report_file):
    cmd = [
      global_vars['Tools']['AIDA64'],
      '/R', report_file,
      '/CUSTOM', config,
      '/TEXT', '/SILENT', '/SAFEST']
    run_program(cmd, check=False)


def run_bleachbit(cleaners=None, preview=True):
  """Run BleachBit preview and save log.

  If preview is True then no files should be deleted."""
  error_path = r'{}\Tools\BleachBit.err'.format(global_vars['LogDir'])
  log_path = error_path.replace('err', 'log')
  extract_item('BleachBit', silent=True)

  # Safety check
  if not cleaners:
    # Disable cleaning and use preset config
    cleaners = ['--preset']
    preview = True

  # Run
  cmd = [
    global_vars['Tools']['BleachBit'],
    '--preview' if preview else '--clean']
  cmd.extend(cleaners)
  out = run_program(cmd, check=False)

  # Save stderr
  if out.stderr.decode().splitlines():
    with open(error_path, 'a', encoding='utf-8') as f:
      for line in out.stderr.decode().splitlines():
        f.write(line.strip() + '\n')

  # Save stdout
  with open(log_path, 'a', encoding='utf-8') as f:
    for line in out.stdout.decode().splitlines():
      f.write(line.strip() + '\n')


def show_disk_usage(disk):
  """Show free and used space for a specified disk."""
  print_standard('{:5}'.format(disk.device.replace('/', ' ')),
    end='', flush=True, timestamp=False)
  try:
    usage = psutil.disk_usage(disk.device)
    display_string = '{percent:>5.2f}% Free  ({free} / {total})'.format(
      percent = 100 - usage.percent,
      free = human_readable_size(usage.free, 2),
      total = human_readable_size(usage.total, 2))
    if usage.percent > 85:
      print_error(display_string, timestamp=False)
    elif usage.percent > 75:
      print_warning(display_string, timestamp=False)
    else:
      print_standard(display_string, timestamp=False)
  except Exception:
    print_warning('Unknown', timestamp=False)


def show_free_space(indent=8, width=32):
  """Show free space info for all fixed disks."""
  message = 'Free Space:'
  for disk in psutil.disk_partitions():
    try:
      if 'fixed' in disk.opts:
        try_and_print(message=message, function=show_disk_usage,
          ns='Unknown', silent_function=False,
          indent=indent, width=width, disk=disk)
        message = ''
    except Exception:
      pass


def show_installed_ram():
  """Show installed RAM."""
  mem = psutil.virtual_memory()
  if mem.total > 5905580032:
    # > 5.5 Gb so 6Gb or greater
    print_standard(human_readable_size(mem.total).strip(), timestamp=False)
  elif mem.total > 3758096384:
    # > 3.5 Gb so 4Gb or greater
    print_warning(human_readable_size(mem.total).strip(), timestamp=False)
  else:
    print_error(human_readable_size(mem.total).strip(), timestamp=False)


def show_os_activation():
  """Show OS activation info."""
  act_str = get_activation_string()
  if windows_is_activated():
    print_standard(act_str, timestamp=False)
  elif re.search(r'unavailable', act_str, re.IGNORECASE):
    print_warning(act_str, timestamp=False)
  else:
    print_error(act_str, timestamp=False)


def show_os_name():
  """Show extended OS name (including warnings)."""
  os_name = global_vars['OS']['DisplayName']
  if global_vars['OS']['Arch'] == 32:
    # Show all 32-bit installs as an error message
    print_error(os_name, timestamp=False)
  else:
    if re.search(
        r'(preview build|unrecognized|unsupported)',
        os_name,
        re.IGNORECASE):
      print_error(os_name, timestamp=False)
    elif re.search(r'outdated', os_name, re.IGNORECASE):
      print_warning(os_name, timestamp=False)
    else:
      print_standard(os_name, timestamp=False)


def show_temp_files_size():
  """Show total size of temp files identified by BleachBit."""
  size_str = None
  total = 0
  with open(r'{LogDir}\Tools\BleachBit.log'.format(**global_vars), 'r') as f:
    for line in f.readlines():
      if re.search(r'^Disk space (to be |)recovered:', line, re.IGNORECASE):
        size = re.sub(r'.*: ', '', line.strip())
        size = re.sub(r'(\w)iB$', r' \1b', size)
        total += convert_to_bytes(size)
        size_str = human_readable_size(total, decimals=1)
  if size_str is None:
    print_warning('UNKNOWN', timestamp=False)
  else:
    print_standard(size_str, timestamp=False)


def show_user_data_summary(indent=8, width=32):
  """Print user data folder sizes for all users."""
  users = get_user_list()
  users = [u for u in users if u['Active']]
  get_user_folder_sizes(users)
  for user in users:
    if ('Size' not in user['Profile']
      and not any(user['Shell Folders'])
      and not any(user['Extra Folders'])):
      # Skip empty users
      continue
    print_success('{indent}User: {user}'.format(
      indent = ' '*int(indent/2),
      user = user['Name']))
    for section in ['Profile', None, 'Shell Folders', 'Extra Folders']:
      folders = []
      if section is None:
        # Divider
        print_standard('{}{}'.format(' '*indent, '-'*(width+6)))
      elif section == 'Profile':
        folders = {'Profile': user['Profile']}
      else:
        folders = user[section]
      for folder in folders:
        print_standard(
          '{indent}{folder:<{width}}{size:>6} ({path})'.format(
            indent =  ' ' * indent,
            width =   width,
            folder =  folder,
            size =    folders[folder].get('Size', 'Unknown'),
            path =    folders[folder].get('Path', 'Unknown')))


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
