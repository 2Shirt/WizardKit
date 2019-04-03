# Wizard Kit: Functions - Data

import ctypes

from functions.json import *
from operator import itemgetter
from settings.data import *


# Classes
class LocalDisk():
  def __init__(self, disk):
    self.disk = disk
    self.name = disk.mountpoint.upper()
    self.path = self.name
  def is_dir(self):
    # Should always be true
    return True
  def is_file(self):
    # Should always be false
    return False


class SourceItem():
  def __init__(self, name, path):
    self.name = name
    self.path = path


# Functions
def cleanup_transfer(dest_path):
  """Fix attributes and move excluded items to separate folder."""
  try:
    # Remove dest_path if empty
    os.rmdir(dest_path)
  except OSError:
    pass
  if not os.path.exists(dest_path):
    # Bail if dest_path was empty and removed
    raise Exception

  # Fix attributes
  cmd = ['attrib', '-a', '-h', '-r', '-s', dest_path]
  run_program(cmd, check=False)

  for root, dirs, files in os.walk(dest_path, topdown=False):
    for name in dirs:
      # Remove empty directories and junction points
      try:
        os.rmdir(os.path.join(root, name))
      except OSError:
        pass
    for name in files:
      # "Remove" files based on exclusion regex
      if REGEX_EXCL_ITEMS.search(name):
        # Make dest folder
        dest_name = root.replace(dest_path, dest_path+'.Removed')
        os.makedirs(dest_name, exist_ok=True)
        # Set dest filename
        dest_name = os.path.join(dest_name, name)
        dest_name = non_clobber_rename(dest_name)
        source_name = os.path.join(root, name)
        try:
          shutil.move(source_name, dest_name)
        except Exception:
          pass


def find_core_storage_volumes(device_path=None):
  """Try to create block devices for any Apple CoreStorage volumes."""
  corestorage_uuid = '53746f72-6167-11aa-aa11-00306543ecac'
  dmsetup_cmd_file = '{TmpDir}/dmsetup_command'.format(**global_vars)

  # Get CoreStorage devices
  cmd = [
    'lsblk', '--json', '--list', '--paths',
    '--output', 'NAME,PARTTYPE']
  if device_path:
    cmd.append(device_path)
  json_data = get_json_from_command(cmd)
  devs = json_data.get('blockdevices', [])
  devs = [d for d in devs if d.get('parttype', '') == corestorage_uuid]
  if devs:
    print_standard(' ')
    print_standard('Detected CoreStorage partition{}'.format(
      '' if len(devs) == 1 else 's'))
    print_standard('  Scanning for inner volume(s)....')

  # Search for inner volumes and setup dev mappers
  for dev in devs:
    dev_path = dev.get('name', '')
    if not dev_path:
      # Can't setup block device without the dev path
      continue
    dev_name = re.sub(r'.*/', '', dev_path)
    log_path = '{LogDir}/testdisk_{dev_name}.log'.format(
      dev_name=dev_name, **global_vars)

    # Run TestDisk
    cmd = [
      'sudo', 'testdisk',
      '/logname', log_path, '/debug', '/log',
      '/cmd', dev_path, 'partition_none,analyze']
    result = run_program(cmd, check=False)
    if result.returncode:
      # i.e. return code is non-zero
      continue
    if not os.path.exists(log_path):
      # TestDisk failed to write log
      continue

    # Check log for found volumes
    cs_vols = {}
    with open(log_path, 'r') as f:
      for line in f.readlines():
        r = re.match(
          r'^.*echo "([^"]+)" . dmsetup create test(\d)$',
          line.strip(),
          re.IGNORECASE)
        if r:
          cs_name = 'CoreStorage_{}_{}'.format(dev_name, r.group(2))
          cs_vols[cs_name] = r.group(1)

    # Create mapper device(s)
    for name, dm_cmd in sorted(cs_vols.items()):
      with open(dmsetup_cmd_file, 'w') as f:
        f.write(dm_cmd)
      cmd = ['sudo', 'dmsetup', 'create', name, dmsetup_cmd_file]
      run_program(cmd, check=False)


def fix_path_sep(path_str):
  """Replace non-native and duplicate dir separators, returns str."""
  return re.sub(r'(\\|/)+', lambda s: os.sep, path_str)


def is_valid_wim_file(item):
  """Checks if the item is a valid WIM file, returns bool."""
  valid = bool(item.is_file() and REGEX_WIM_FILE.search(item.name))
  if valid:
    extract_item('wimlib', silent=True)
    cmd = [global_vars['Tools']['wimlib-imagex'], 'info', item.path]
    try:
      run_program(cmd)
    except subprocess.CalledProcessError:
      valid = False
      print_log('WARNING: Image "{}" damaged.'.format(item.name))
  return valid


def get_mounted_volumes():
  """Get mounted volumes, returns dict."""
  cmd = [
    'findmnt', '-J', '-b', '-i',
    '-t', (
      'autofs,binfmt_misc,bpf,cgroup,cgroup2,configfs,debugfs,devpts,'
      'devtmpfs,hugetlbfs,mqueue,proc,pstore,securityfs,sysfs,tmpfs'
      ),
    '-o', 'SOURCE,TARGET,FSTYPE,LABEL,SIZE,AVAIL,USED']
  json_data = get_json_from_command(cmd)
  mounted_volumes = []
  for item in json_data.get('filesystems', []):
    mounted_volumes.append(item)
    mounted_volumes.extend(item.get('children', []))
  return {item['source']: item for item in mounted_volumes}


def mount_volumes(
    all_devices=True, device_path=None,
    read_write=False, core_storage=True):
  """Mount all detected filesystems."""
  report = {}
  cmd = [
    'lsblk', '--json', '--paths',
    '--output', 'NAME,FSTYPE,LABEL,UUID,PARTTYPE,TYPE,SIZE']
  if not all_devices and device_path:
    # Only mount volumes for specific device
    cmd.append(device_path)

  # Check for Apple CoreStorage volumes first
  if core_storage:
    find_core_storage_volumes(device_path)

  # Get list of block devices
  json_data = get_json_from_command(cmd)
  devs = json_data.get('blockdevices', [])

  # Get list of volumes
  volumes = {}
  for dev in devs:
    if not dev.get('children', []):
      volumes.update({dev['name']: dev})
    for child in dev.get('children', []):
      if not child.get('children', []):
        volumes.update({child['name']: child})
      for grandchild in child.get('children', []):
        volumes.update({grandchild['name']: grandchild})

  # Get list of mounted volumes
  mounted_volumes = get_mounted_volumes()

  # Loop over volumes
  for vol_path, vol_data in volumes.items():
    vol_data['show_data'] = {
      'message': vol_path.replace('/dev/mapper/', ''),
      'data': None,
      }
    if re.search(r'^loop\d', vol_path, re.IGNORECASE):
      # Skip loopback devices
      vol_data['show_data']['data'] = 'Skipped'
      vol_data['show_data']['warning'] = True
      report[vol_path] = vol_data
    elif 'children' in vol_data:
      # Skip LVM/RAID partitions (the real volume is mounted separately)
      vol_data['show_data']['data'] = vol_data.get('fstype', 'UNKNOWN')
      if vol_data.get('label', None):
        vol_data['show_data']['data'] += ' "{}"'.format(vol_data['label'])
      vol_data['show_data']['info'] = True
      report[vol_path] = vol_data
    else:
      if vol_path in mounted_volumes:
        vol_data['show_data']['warning'] = True
      else:
        # Mount volume
        cmd = ['udevil', 'mount',
          '-o', 'rw' if read_write else 'ro',
          vol_path]
        try:
          run_program(cmd)
        except subprocess.CalledProcessError:
          vol_data['show_data']['data'] = 'Failed to mount'
          vol_data['show_data']['error'] = True
      # Update mounted_volumes data
      mounted_volumes = get_mounted_volumes()

      # Format pretty result string
      if vol_data['show_data']['data'] == 'Failed to mount':
        vol_data['mount_point'] = None
      else:
        size_used = human_readable_size(
          mounted_volumes[vol_path]['used'])
        size_avail = human_readable_size(
          mounted_volumes[vol_path]['avail'])
        vol_data['size_avail'] = size_avail
        vol_data['size_used'] = size_used
        vol_data['mount_point'] = mounted_volumes[vol_path]['target']
        vol_data['show_data']['data'] = 'Mounted on {}'.format(
          mounted_volumes[vol_path]['target'])
        vol_data['show_data']['data'] = '{:40} ({} used, {} free)'.format(
          vol_data['show_data']['data'],
          size_used,
          size_avail)

      # Update report
      report[vol_path] = vol_data

  return report


def mount_backup_shares(read_write=False):
  """Mount the backup shares unless labeled as already mounted."""
  if psutil.LINUX:
    mounted_volumes = get_mounted_volumes()
  for server in BACKUP_SERVERS:
    if psutil.LINUX:
      # Update mounted status
      source = '//{IP}/{Share}'.format(**server)
      dest = '/Backups/{Name}'.format(**server)
      mounted_str = '(Already) Mounted {}'.format(dest)
      data = mounted_volumes.get(source, {})
      if dest == data.get('target', ''):
        server['Mounted'] = True
    elif psutil.WINDOWS:
      mounted_str = '(Already) Mounted {Name}'.format(**server)
    if server['Mounted']:
      print_warning(mounted_str)
      continue

    mount_network_share(server, read_write)


def mount_network_share(server, read_write=False):
  """Mount a network share defined by server."""
  if read_write:
    username = server['RW-User']
    password = server['RW-Pass']
  else:
    username = server['User']
    password = server['Pass']
  if psutil.WINDOWS:
    cmd = [
      'net', 'use', r'\\{IP}\{Share}'.format(**server),
      '/user:{}'.format(username), password]
    warning = r'Failed to mount \\{Name}\{Share}, {IP} unreachable.'.format(
      **server)
    error = r'Failed to mount \\{Name}\{Share} ({IP})'.format(**server)
    success = 'Mounted {Name}'.format(**server)
  elif psutil.LINUX:
    cmd = [
      'sudo', 'mkdir', '-p',
      '/Backups/{Name}'.format(**server)]
    run_program(cmd)
    cmd = [
      'sudo', 'mount',
      '//{IP}/{Share}'.format(**server),
      '/Backups/{Name}'.format(**server),
      '-o', '{}username={},password={}'.format(
        '' if read_write else 'ro,',
        username,
        password)]
    warning = 'Failed to mount /Backups/{Name}, {IP} unreachable.'.format(
      **server)
    error = 'Failed to mount /Backups/{Name}'.format(**server)
    success = 'Mounted /Backups/{Name}'.format(**server)

  # Test connection
  try:
    ping(server['IP'])
  except subprocess.CalledProcessError:
    print_warning(warning)
    sleep(1)
    return False

  # Mount
  try:
    run_program(cmd)
  except Exception:
    print_error(error)
    sleep(1)
  else:
    print_info(success)
    server['Mounted'] = True


def run_fast_copy(items, dest):
  """Copy items to dest using FastCopy."""
  if not items:
    raise Exception

  cmd = [global_vars['Tools']['FastCopy'], *FAST_COPY_ARGS]
  cmd.append(r'/logfile={LogDir}\Tools\FastCopy.log'.format(**global_vars))
  cmd.extend(items)
  cmd.append('/to={}\\'.format(dest))

  run_program(cmd)


def run_wimextract(source, items, dest):
  """Extract items from source WIM to dest folder."""
  if not items:
    raise Exception
  extract_item('wimlib', silent=True)

  # Write files.txt
  with open(r'{}\wim_files.txt'.format(global_vars['TmpDir']), 'w',
    encoding='utf-8') as f:
    # Defaults
    for item in items:
      f.write('{}\n'.format(item))
  sleep(1) # For safety?

  # Extract files
  cmd = [
    global_vars['Tools']['wimlib-imagex'],
    'extract',
    source, '1',
    r'@{}\wim_files.txt'.format(global_vars['TmpDir']),
    '--dest-dir={}\\'.format(dest),
    '--no-acls',
    '--nullglob']
  run_program(cmd)


def list_source_items(source_obj, rel_path=None):
  """List items in a dir or WIM, returns list of SourceItem objects."""
  items = []
  rel_path = '{}{}'.format(os.sep, rel_path) if rel_path else ''
  if source_obj.is_dir():
    source_path = '{}{}'.format(source_obj.path, rel_path)
    items = [SourceItem(name=item.name, path=item.path)
      for item in os.scandir(source_path)]
  else:
    # Prep wimlib-imagex
    if psutil.WINDOWS:
      extract_item('wimlib', silent=True)
    cmd = [
      global_vars['Tools']['wimlib-imagex'], 'dir',
      source_obj.path, '1']
    if rel_path:
      cmd.append('--path={}'.format(rel_path))

    # Get item list
    try:
      items = run_program(cmd)
    except subprocess.CalledProcessError:
      print_error('ERROR: Failed to get file list.')
      raise

    # Strip non-root items
    items = [fix_path_sep(i.strip())
      for i in items.stdout.decode('utf-8', 'ignore').splitlines()]
    if rel_path:
      items = [i.replace(rel_path, '') for i in items]
    items = [i for i in items
      if i.count(os.sep) == 1 and i.strip() != os.sep]
    items = [SourceItem(name=i[1:], path=rel_path+i) for i in items]

  # Done
  return items


def scan_source(source_obj, dest_path, rel_path='', interactive=True):
  """Scan source for files/folders to transfer, returns list.

  This will scan the root and (recursively) any Windows.old folders."""
  selected_items = []
  win_olds = []

  # Root Items
  root_items = []
  item_list = list_source_items(source_obj, rel_path)
  for item in item_list:
    if REGEX_WINDOWS_OLD.search(item.name):
      item.name = '{}{}{}'.format(
        rel_path,
        os.sep if rel_path else '',
        item.name)
      win_olds.append(item)
    elif REGEX_INCL_ROOT_ITEMS.search(item.name):
      print_success('Auto-Selected: {}'.format(item.path))
      root_items.append('{}'.format(item.path))
    elif not REGEX_EXCL_ROOT_ITEMS.search(item.name):
      if not interactive:
        print_success('Auto-Selected: {}'.format(item.path))
        root_items.append('{}'.format(item.path))
      else:
        prompt = 'Transfer: "{}{}{}" ?'.format(
          rel_path,
          os.sep if rel_path else '',
          item.name)
        choices = ['Yes', 'No', 'All', 'Quit']
        answer = choice(prompt=prompt, choices=choices)
        if answer == 'Quit':
          abort()
        elif answer == 'All':
          interactive = False
        if answer in ['Yes', 'All']:
          root_items.append('{}'.format(item.path))
  if root_items:
    selected_items.append({
      'Message':    '{}{}Root Items...'.format(
        rel_path,
        ' ' if rel_path else ''),
      'Items':    root_items.copy(),
      'Destination':  dest_path})

  # Fonts
  font_obj = get_source_item_obj(source_obj, rel_path, 'Windows/Fonts')
  if font_obj:
    selected_items.append({
      'Message':    '{}{}Fonts...'.format(
        rel_path,
        ' ' if rel_path else ''),
      'Items':    [font_obj.path],
      'Destination':  '{}{}Windows'.format(
        dest_path, os.sep)})

  # Registry
  registry_items = []
  for folder in ['config', 'OEM']:
    folder_obj = get_source_item_obj(
      source_obj, rel_path, 'Windows/System32/{}'.format(folder))
    if folder_obj:
      registry_items.append(folder_obj.path)
  if registry_items:
    selected_items.append({
      'Message':    '{}{}Registry...'.format(
        rel_path,
        ' ' if rel_path else ''),
      'Items':    registry_items.copy(),
      'Destination':  '{}{}Windows{}System32'.format(
        dest_path, os.sep, os.sep)})

  # Windows.old(s)
  for old in win_olds:
    selected_items.extend(scan_source(
      source_obj,
      '{}{}{}'.format(dest_path, os.sep, old.name),
      rel_path=old.name,
      interactive=False))

  # Done
  return selected_items


def get_source_item_obj(source_obj, rel_path, item_path):
  """Check if the item exists, returns SourceItem object or None."""
  item_obj = None
  item_path = fix_path_sep(item_path)
  if source_obj.is_dir():
    item_obj = SourceItem(
      name = item_path,
      path = '{}{}{}{}{}'.format(
        source_obj.path,
        os.sep,
        rel_path,
        os.sep if rel_path else '',
        item_path))
    if not os.path.exists(item_obj.path):
      item_obj = None
  else:
    # Assuming WIM file
    if psutil.WINDOWS:
      extract_item('wimlib', silent=True)
    cmd = [
      global_vars['Tools']['wimlib-imagex'], 'dir',
      source_obj.path, '1',
      '--path={}'.format(item_path),
      '--one-file-only']
    try:
      run_program(cmd)
    except subprocess.CalledProcessError:
      # function will return None below
      pass
    else:
      item_obj = SourceItem(
        name = item_path,
        path = '{}{}{}{}'.format(
          os.sep,
          rel_path,
          os.sep if rel_path else '',
          item_path))
  return item_obj


def select_destination(folder_path, prompt='Select destination'):
  """Select destination drive, returns path as string."""
  disk = select_volume(prompt)
  if 'fixed' not in disk['Disk'].opts:
    folder_path = folder_path.replace('\\', '-')
  path = '{disk}{folder_path}_{Date}'.format(
    disk = disk['Disk'].mountpoint,
    folder_path = folder_path,
    **global_vars)

  # Avoid merging with existing folder
  path = non_clobber_rename(path)
  os.makedirs(path, exist_ok=True)

  return path


def select_source(backup_prefix):
  """Select matching backup from BACKUP_SERVERS, returns obj."""
  selected_source = None
  local_sources = []
  remote_sources = []
  sources = []
  mount_backup_shares(read_write=False)

  # Check for prefix folders on servers
  for server in BACKUP_SERVERS:
    if server['Mounted']:
      print_standard('Scanning {}...'.format(server['Name']))
      for d in os.scandir(r'\\{IP}\{Share}'.format(**server)):
        if (d.is_dir()
          and d.name.lower().startswith(backup_prefix.lower())):
          # Add folder to remote_sources
          remote_sources.append({
            'Name': '{:9}| File-Based:   [DIR]  {}'.format(
              server['Name'], d.name),
            'Server': server,
            'Sort': d.name,
            'Source': d})

  # Check for images and subfolders
  for prefix_path in remote_sources.copy():
    for item in os.scandir(prefix_path['Source'].path):
      if item.is_dir():
        # Add folder to remote_sources
        remote_sources.append({
          'Name': r'{:9}| File-Based:   [DIR]  {}\{}'.format(
            prefix_path['Server']['Name'],  # Server
            prefix_path['Source'].name,   # Prefix folder
            item.name,            # Sub-folder
            ),
          'Server': prefix_path['Server'],
          'Sort': r'{}\{}'.format(
            prefix_path['Source'].name,   # Prefix folder
            item.name,            # Sub-folder
            ),
          'Source': item})

        # Check for images in folder
        for subitem in os.scandir(item.path):
          if REGEX_WIM_FILE.search(item.name):
            # Add image to remote_sources
            try:
              size = human_readable_size(item.stat().st_size)
            except Exception:
              size = '  ?  ?' # unknown
            remote_sources.append({
              'Disabled': bool(not is_valid_wim_file(subitem)),
              'Name': r'{:9}| Image-Based:  {:>7}  {}\{}\{}'.format(
                prefix_path['Server']['Name'],  # Server
                size,               # Size (duh)
                prefix_path['Source'].name,   # Prefix folder
                item.name,            # Sub-folder
                subitem.name,           # Image file
                ),
              'Server': prefix_path['Server'],
              'Sort': r'{}\{}\{}'.format(
                prefix_path['Source'].name,   # Prefix folder
                item.name,            # Sub-folder
                subitem.name,           # Image file
                ),
              'Source': subitem})
      elif REGEX_WIM_FILE.search(item.name):
        # Add image to remote_sources
        try:
          size = human_readable_size(item.stat().st_size)
        except Exception:
          size = '  ?  ?' # unknown
        remote_sources.append({
          'Disabled': bool(not is_valid_wim_file(item)),
          'Name': r'{:9}| Image-Based:  {:>7}  {}\{}'.format(
            prefix_path['Server']['Name'],  # Server
            size,               # Size (duh)
            prefix_path['Source'].name,   # Prefix folder
            item.name,            # Image file
            ),
          'Server': prefix_path['Server'],
          'Sort': r'{}\{}'.format(
            prefix_path['Source'].name,   # Prefix folder
            item.name,            # Image file
            ),
          'Source': item})

  # Check for local sources
  print_standard('Scanning for local sources...')
  set_thread_error_mode(silent=True) # Prevents "No disk" popups
  sys_drive = global_vars['Env']['SYSTEMDRIVE']
  for d in psutil.disk_partitions():
    if re.search(r'^{}'.format(sys_drive), d.mountpoint, re.IGNORECASE):
      # Skip current OS drive
      continue
    if 'fixed' in d.opts:
      # Skip DVD, etc
      local_sources.append({
        'Name': '{:9}| File-Based:   [DISK] {}'.format(
          '  Local', d.mountpoint),
        'Sort': d.mountpoint,
        'Source': LocalDisk(d)})
      # Check for images and subfolders
      for item in os.scandir(d.mountpoint):
        if REGEX_WIM_FILE.search(item.name):
          try:
            size = human_readable_size(item.stat().st_size)
          except Exception:
            size = '  ?  ?' # unknown
          local_sources.append({
            'Disabled': bool(not is_valid_wim_file(item)),
            'Name': r'{:9}| Image-Based:  {:>7}  {}{}'.format(
              '  Local', size, d.mountpoint, item.name),
            'Sort': r'{}{}'.format(d.mountpoint, item.name),
            'Source': item})
        elif REGEX_EXCL_ROOT_ITEMS.search(item.name):
          pass
        elif REGEX_EXCL_ITEMS.search(item.name):
          pass
        elif item.is_dir():
          # Add folder to local_sources
          local_sources.append({
            'Name': r'{:9}| File-Based:   [DIR]  {}{}'.format(
              '  Local', d.mountpoint, item.name),
            'Sort': r'{}{}'.format(d.mountpoint, item.name),
            'Source': item})

  set_thread_error_mode(silent=False) # Return to normal

  # Build Menu
  local_sources.sort(key=itemgetter('Sort'))
  remote_sources.sort(key=itemgetter('Sort'))
  sources.extend(local_sources)
  sources.extend(remote_sources)
  actions = [{'Name': 'Quit', 'Letter': 'Q'}]

  # Select backup from sources
  if len(sources) > 0:
    selection = menu_select(
      'Which backup are we using?',
      main_entries=sources,
      action_entries=actions,
      disabled_label='DAMAGED')
    if selection == 'Q':
      umount_backup_shares()
      exit_script()
    else:
      selected_source = sources[int(selection)-1]['Source']
  else:
    print_error('ERROR: No backups found using prefix: {}.'.format(
      backup_prefix))
    umount_backup_shares()
    pause("Press Enter to exit...")
    exit_script()

  # Sanity check
  if selected_source.is_file():
    # Image-Based
    if not REGEX_WIM_FILE.search(selected_source.name):
      print_error('ERROR: Unsupported image: {}'.format(
        selected_source.path))
      raise GenericError

  # Done
  return selected_source


def select_volume(title='Select disk', auto_select=True):
  """Select disk from attached disks. returns dict."""
  actions =   [{'Name': 'Quit', 'Letter': 'Q'}]
  disks =   []

  # Build list of disks
  set_thread_error_mode(silent=True) # Prevents "No disk" popups
  for d in psutil.disk_partitions():
    info = {
      'Disk': d,
      'Name': d.mountpoint}
    try:
      usage = psutil.disk_usage(d.device)
      free = '{free} / {total} available'.format(
        free = human_readable_size(usage.free, 2),
        total = human_readable_size(usage.total, 2))
    except Exception:
      # Meh, leaving unsupported destinations out
      pass
      # free = 'Unknown'
      # info['Disabled'] = True
    else:
      info['Display Name'] = '{}  ({})'.format(info['Name'], free)
      disks.append(info)
  set_thread_error_mode(silent=False) # Return to normal

  # Skip menu?
  if len(disks) == 1 and auto_select:
    return disks[0]

  # Show menu
  selection = menu_select(title, main_entries=disks, action_entries=actions)
  if selection == 'Q':
    exit_script()
  else:
    return disks[int(selection)-1]


def set_thread_error_mode(silent=True):
  """Disable or Enable Windows error message dialogs.

  Disable when scanning disks to avoid popups for empty cardreaders, etc
  """
  # Code borrowed from: https://stackoverflow.com/a/29075319
  kernel32 = ctypes.WinDLL('kernel32')

  if silent:
    kernel32.SetThreadErrorMode(SEM_FAIL, ctypes.byref(SEM_NORMAL))
  else:
    kernel32.SetThreadErrorMode(SEM_NORMAL, ctypes.byref(SEM_NORMAL))


def transfer_source(source_obj, dest_path, selected_items):
  """Transfer, or extract, files/folders from source to destination."""
  if source_obj.is_dir():
    # Run FastCopy for each selection "group"
    for group in selected_items:
      try_and_print(message=group['Message'],
        function=run_fast_copy, cs='Done',
        items=group['Items'],
        dest=group['Destination'])
  else:
    if REGEX_WIM_FILE.search(source_obj.name):
      # Extract files from WIM
      for group in selected_items:
        try_and_print(message=group['Message'],
          function=run_wimextract, cs='Done',
          source=source_obj.path,
          items=group['Items'],
          dest=dest_path)
    else:
      print_error('ERROR: Unsupported image: {}'.format(source_obj.path))
      raise GenericError


def umount_backup_shares():
  """Unmount the backup shares regardless of current status."""
  for server in BACKUP_SERVERS:
    umount_network_share(server)


def umount_network_share(server):
  """Unmount a network share defined by server."""
  cmd = r'net use \\{IP}\{Share} /delete'.format(**server)
  cmd = cmd.split(' ')
  try:
    run_program(cmd)
  except Exception:
    print_error(r'Failed to umount \\{Name}\{Share}.'.format(**server))
    sleep(1)
  else:
    print_info('Umounted {Name}'.format(**server))
    server['Mounted'] = False


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
