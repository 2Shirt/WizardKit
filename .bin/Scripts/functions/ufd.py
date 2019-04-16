"""Wizard Kit: Functions - UFD"""
# pylint: disable=broad-except,wildcard-import
# vim: sts=2 sw=2 ts=2

import os
import re
import shutil
import pathlib
from collections import OrderedDict
from functions.common import *


def case_insensitive_search(path, item):
  """Search path for item case insensitively, returns str."""
  regex_match = '^{}$'.format(item)
  real_path = ''

  # Quick check first
  if os.path.exists('{}/{}'.format(path, item)):
    real_path = '{}{}{}'.format(
      path,
      '' if path == '/' else '/',
      item,
      )

  # Check all items in dir
  for entry in os.scandir(path):
    if re.match(regex_match, entry.name, re.IGNORECASE):
      real_path = '{}{}{}'.format(
        path,
        '' if path == '/' else '/',
        entry.name,
        )

  # Done
  if not real_path:
    raise FileNotFoundError('{}/{}'.format(path, item))

  return real_path


def confirm_selections(args):
  """Ask tech to confirm selections, twice if necessary."""
  if not ask('Is the above information correct?'):
    abort(False)
  ## Safety check
  if not args['--update']:
    print_standard(' ')
    print_warning('SAFETY CHECK')
    print_standard(
      'All data will be DELETED from the disk and partition(s) listed above.')
    print_standard(
      'This is irreversible and will lead to {RED}DATA LOSS.{CLEAR}'.format(
        **COLORS))
    if not ask('Asking again to confirm, is this correct?'):
      abort(False)

  print_standard(' ')


def copy_source(source, items, overwrite=False):
  """Mount source and copy items to /mnt/UFD."""
  os.makedirs('/mnt/Source', exist_ok=True)
  mount(source, '/mnt/Source')
  for i_source, i_dest in items:
    i_source = '/mnt/Source{}'.format(i_source)
    i_dest = '/mnt/UFD{}'.format(i_dest)
    recursive_copy(i_source, i_dest, overwrite=overwrite)
  unmount('/mnt/Source')


def find_path(path):
  """Find path case-insensitively, returns pathlib.Path obj."""
  path_obj = pathlib.Path(path).resolve()

  # Quick check first
  if path_obj.exists():
    return path_obj

  # Fix case
  parts = path_obj.relative_to('/').parts
  real_path = '/'
  for part in parts:
    try:
      real_path = case_insensitive_search(real_path, part)
    except NotADirectoryError:
      # Reclassify error
      raise FileNotFoundError(path)

  # Raise error if path doesn't exist
  path_obj = pathlib.Path(real_path)
  if not path_obj.exists():
    raise FileNotFoundError(path_obj)

  # Done
  return path_obj


def get_user_home(user):
  """Get path to user's home dir, returns str."""
  home_dir = None
  cmd = ['getent', 'passwd', user]
  result = run_program(cmd, encoding='utf-8', errors='ignore', check=False)
  try:
    home_dir = result.stdout.split(':')[5]
  except Exception:
    # Just use HOME from ENV (or '/root' if that fails)
    home_dir = os.environ.get('HOME', '/root')

  return home_dir


def get_user_name():
  """Get real user name, returns str."""
  user = None
  if 'SUDO_USER' in os.environ:
    user = os.environ.get('SUDO_USER', 'Unknown')
  else:
    user = os.environ.get('USER', 'Unknown')

  return user


def is_valid_path(path_obj, path_type):
  """Verify path_obj is valid by type, returns bool."""
  valid_path = False
  if path_type == 'DIR':
    valid_path = path_obj.is_dir()
  elif path_type == 'KIT':
    valid_path = path_obj.is_dir() and path_obj.joinpath('.bin').exists()
  elif path_type == 'ISO':
    valid_path = path_obj.is_file() and path_obj.suffix.lower() == '.iso'
  elif path_type == 'UFD':
    valid_path = path_obj.is_block_device()

  return valid_path


def mount(mount_source, mount_point):
  """Mount mount_source on mount_point."""
  os.makedirs(mount_point, exist_ok=True)
  cmd = ['mount', mount_source, mount_point]
  run_program(cmd)


def unmount(mount_point):
  """Unmount mount_point."""
  cmd = ['umount', mount_point]
  run_program(cmd)


def prep_device(dev_path, label, use_mbr=False):
  """Format device in preparation for applying the WizardKit components

  This is done is four steps:
  1. Zero-out first 64MB (this deletes the partition table and/or bootloader)
  2. Create a new partition table (GPT by default, optionally MBR)
  3. Set boot flag
  4. Format partition (FAT32, 4K aligned)
  """
  # Zero-out first 64MB
  cmd = 'dd bs=4M count=16 if=/dev/zero of={}'.format(dev_path).split()
  try_and_print(
    message='Zeroing first 64MB...',
    function=run_program,
    cmd=cmd,
    )

  # Create partition table
  cmd = 'parted {} --script -- mklabel {} mkpart primary fat32 4MiB {}'.format(
    dev_path,
    'msdos' if use_mbr else 'gpt',
    '-1s' if use_mbr else '-4MiB',
    ).split()
  try_and_print(
    message='Creating partition table...',
    function=run_program,
    cmd=cmd,
    )

  # Set boot flag
  cmd = 'parted {} set 1 {} on'.format(
    dev_path,
    'boot' if use_mbr else 'legacy_boot',
    ).split()
  try_and_print(
    message='Setting boot flag...',
    function=run_program,
    cmd=cmd,
    )

  # Find partition
  cmd = [
    'lsblk',
    '--list',
    '--noheadings',
    '--output', 'name',
    '--paths',
    dev_path,
    ]
  result = run_program(cmd, encoding='utf-8', errors='ignore')
  part_path = result.stdout.splitlines()[-1].strip()

  # Format partition
  cmd = [
    'mkfs.vfat', '-F', '32',
    '-n', label,
    part_path,
    ]
  try_and_print(
    message='Formatting partition...',
    function=run_program,
    cmd=cmd,
    )


def recursive_copy(source, dest, overwrite=False):
  """Copy source to dest recursively.

  NOTE: This uses rsync style source/dest syntax.
  If the source has a trailing slash then it's contents are copied,
  otherwise the source itself is copied.

  Examples assuming "ExDir/ExFile.txt" exists:
  recursive_copy("ExDir", "Dest/") results in "Dest/ExDir/ExFile.txt"
  recursive_copy("ExDir/", "Dest/") results in "Dest/ExFile.txt"

  NOTE 2: dest does not use find_path because it might not exist.
  """
  copy_contents = source.endswith('/')
  source = find_path(source)
  dest = pathlib.Path(dest).resolve().joinpath(source.name)
  os.makedirs(dest.parent, exist_ok=True)

  if source.is_dir():
    if copy_contents:
      # Trailing slash syntax
      for item in os.scandir(source):
        recursive_copy(item.path, dest.parent, overwrite=overwrite)
    elif not dest.exists():
      # No conflict, copying whole tree (no merging needed)
      shutil.copytree(source, dest)
    elif not dest.is_dir():
      # Refusing to replace file with dir
      raise FileExistsError('Refusing to replace file: {}'.format(dest))
    else:
      # Dest exists and is a dir, merge dirs
      for item in os.scandir(source):
        recursive_copy(item.path, dest, overwrite=overwrite)
  elif source.is_file():
    if not dest.exists():
      # No conflict, copying file
      shutil.copy2(source, dest)
    elif not dest.is_file():
      # Refusing to replace dir with file
      raise FileExistsError('Refusing to replace dir: {}'.format(dest))
    elif overwrite:
      # Dest file exists, deleting and replacing file
      os.remove(dest)
      shutil.copy2(source, dest)
    else:
      # Refusing to delete file when overwrite=False
      raise FileExistsError('Refusing to delete file: {}'.format(dest))


def running_as_root():
  """Check if running with effective UID of 0, returns bool."""
  return os.geteuid() == 0


def show_selections(args, sources, ufd_dev, ufd_sources):
  """Show selections including non-specified options."""

  # Sources
  print_info('Sources')
  for label in ufd_sources.keys():
    if label in sources:
      print_standard('  {label:<18} {path}'.format(
        label=label+':',
        path=sources[label],
        ))
    else:
      print_standard('  {label:<18} {YELLOW}Not Specified{CLEAR}'.format(
        label=label+':',
        **COLORS,
        ))
  print_standard(' ')

  # Destination
  print_info('Destination')
  cmd = [
    'lsblk', '--nodeps', '--noheadings', '--paths',
    '--output', 'NAME,FSTYPE,TRAN,SIZE,VENDOR,MODEL,SERIAL',
    ufd_dev,
    ]
  result = run_program(cmd, check=False, encoding='utf-8', errors='ignore')
  print_standard(result.stdout.strip())
  cmd = [
    'lsblk', '--noheadings', '--paths',
    '--output', 'NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT',
    ufd_dev,
    ]
  result = run_program(cmd, check=False, encoding='utf-8', errors='ignore')
  for line in result.stdout.splitlines()[1:]:
    print_standard(line)

  # Notes
  if args['--update']:
    print_warning('Updating kit in-place')
  elif args['--use-mbr']:
    print_warning('Formatting using legacy MBR')
  print_standard(' ')


def verify_sources(args, ufd_sources):
  """Check all sources and abort if necessary, returns dict."""
  sources = OrderedDict()

  for label, data in ufd_sources.items():
    s_path = args[data['Arg']]
    if s_path:
      try:
        s_path_obj = find_path(s_path)
      except FileNotFoundError:
        print_error('ERROR: {} not found: {}'.format(label, s_path))
        abort(False)
      if not is_valid_path(s_path_obj, data['Type']):
        print_error('ERROR: Invalid {} source: {}'.format(label, s_path))
        abort(False)
      sources[label] = s_path_obj

  return sources


def verify_ufd(dev_path):
  """Check that dev_path is a valid UFD, returns pathlib.Path obj."""
  ufd_dev = None

  try:
    ufd_dev = find_path(dev_path)
  except FileNotFoundError:
    print_error('ERROR: UFD device not found: {}'.format(dev_path))
    abort(False)

  if not is_valid_path(ufd_dev, 'UFD'):
    print_error('ERROR: Invalid UFD device: {}'.format(ufd_dev))
    abort(False)

  return ufd_dev


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
