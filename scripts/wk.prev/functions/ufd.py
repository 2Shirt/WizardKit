"""Wizard Kit: Functions - UFD"""
# pylint: disable=broad-except,wildcard-import
# vim: sts=2 sw=2 ts=2

import os
import re
import shutil
import pathlib
from collections import OrderedDict
from functions.common import *


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
  """Copy source items to /mnt/UFD."""
  is_image = source.is_file()

  # Mount source if necessary
  if is_image:
    mount(source, '/mnt/Source')

  # Copy items
  for i_source, i_dest in items:
    i_source = '{}{}'.format(
      '/mnt/Source' if is_image else source,
      i_source,
      )
    i_dest = '/mnt/UFD{}'.format(i_dest)
    try:
      recursive_copy(i_source, i_dest, overwrite=overwrite)
    except FileNotFoundError:
      # Going to assume (hope) that this is fine
      pass

  # Unmount source if necessary
  if is_image:
    unmount('/mnt/Source')


def find_first_partition(dev_path):
  """Find path to first partition of dev, returns str."""
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

  return part_path


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


def hide_items(ufd_dev, items):
  """Set FAT32 hidden flag for items."""
  # pylint: disable=invalid-name
  with open('/root/.mtoolsrc', 'w') as f:
    f.write('drive U: file="{}"\n'.format(
      find_first_partition(ufd_dev)))
    f.write('mtools_skip_check=1\n')

  # Hide items
  for item in items:
    cmd = ['yes | mattrib +h "U:/{}"'.format(item)]
    run_program(cmd, check=False, shell=True)


def install_syslinux_to_dev(ufd_dev, use_mbr):
  """Install Syslinux to UFD (dev)."""
  cmd = [
    'dd',
    'bs=440',
    'count=1',
    'if=/usr/lib/syslinux/bios/{}.bin'.format(
      'mbr' if use_mbr else 'gptmbr',
      ),
    'of={}'.format(ufd_dev),
    ]
  run_program(cmd)


def install_syslinux_to_partition(partition):
  """Install Syslinux to UFD (partition)."""
  cmd = [
    'syslinux',
    '--install',
    '--directory',
    '/arch/boot/syslinux/',
    partition,
    ]
  run_program(cmd)


def is_valid_path(path_obj, path_type):
  """Verify path_obj is valid by type, returns bool."""
  valid_path = False
  if path_type == 'DIR':
    valid_path = path_obj.is_dir()
  elif path_type == 'KIT':
    valid_path = path_obj.is_dir() and path_obj.joinpath('.bin').exists()
  elif path_type == 'IMG':
    valid_path = path_obj.is_file() and path_obj.suffix.lower() == '.img'
  elif path_type == 'ISO':
    valid_path = path_obj.is_file() and path_obj.suffix.lower() == '.iso'
  elif path_type == 'UFD':
    valid_path = path_obj.is_block_device()

  return valid_path


def mount(mount_source, mount_point, read_write=False):
  """Mount mount_source on mount_point."""
  os.makedirs(mount_point, exist_ok=True)
  cmd = [
    'mount',
    mount_source,
    mount_point,
    '-o',
    'rw' if read_write else 'ro',
    ]
  run_program(cmd)


def prep_device(dev_path, label, use_mbr=False, indent=2):
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
    indent=indent,
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
    indent=indent,
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
    indent=indent,
    message='Setting boot flag...',
    function=run_program,
    cmd=cmd,
    )

  # Format partition
  cmd = [
    'mkfs.vfat', '-F', '32',
    '-n', label,
    find_first_partition(dev_path),
    ]
  try_and_print(
    indent=indent,
    message='Formatting partition...',
    function=run_program,
    cmd=cmd,
    )


def remove_arch():
  """Remove arch dir from UFD.

  This ensures a clean installation to the UFD and resets the boot files
  """
  shutil.rmtree(find_path('/mnt/UFD/arch'))


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


def unmount(mount_point):
  """Unmount mount_point."""
  cmd = ['umount', mount_point]
  run_program(cmd)


def update_boot_entries(boot_entries, boot_files, iso_label, ufd_label):
  """Update boot files for UFD usage"""
  configs = []

  # Find config files
  for c_path, c_ext in boot_files.items():
    c_path = find_path('/mnt/UFD{}'.format(c_path))
    for item in os.scandir(c_path):
      if item.name.lower().endswith(c_ext.lower()):
        configs.append(item.path)

  # Update Linux labels
  cmd = [
    'sed',
    '--in-place',
    '--regexp-extended',
    's/{}/{}/'.format(iso_label, ufd_label),
    *configs,
    ]
  run_program(cmd)

  # Uncomment extra entries if present
  for b_path, b_comment in boot_entries.items():
    try:
      find_path('/mnt/UFD{}'.format(b_path))
    except (FileNotFoundError, NotADirectoryError):
      # Entry not found, continue to next entry
      continue

    # Entry found, update config files
    cmd = [
      'sed',
      '--in-place',
      's/#{}#//'.format(b_comment),
      *configs,
      ]
    run_program(cmd, check=False)


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
