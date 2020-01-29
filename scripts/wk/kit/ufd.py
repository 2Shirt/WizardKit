"""WizardKit: UFD Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import shutil

from collections import OrderedDict
from docopt import docopt

from wk import io, log, std
from wk.cfg.main import KIT_NAME_FULL, KIT_NAME_SHORT
from wk.cfg.ufd import BOOT_ENTRIES, BOOT_FILES, ITEMS, ITEMS_HIDDEN, SOURCES
from wk.exe import run_program
from wk.os import linux


# STATIC VARIABLES
DOCSTRING = '''WizardKit: Build UFD

Usage:
  build-ufd [options] --ufd-device PATH --linux PATH
            [--linux-minimal PATH]
            [--main-kit PATH]
            [--winpe PATH]
            [--extra-dir PATH]
  build-ufd (-h | --help)

Options:
  -e PATH, --extra-dir PATH
  -k PATH, --main-kit PATH
  -l PATH, --linux PATH
  -m PATH, --linux-minimal PATH
  -u PATH, --ufd-device PATH
  -w PATH, --winpe PATH

  -h --help             Show this page
  -M --use-mbr          Use real MBR instead of GPT w/ Protective MBR
  -F --force            Bypass all confirmation messages. USE WITH EXTREME CAUTION!
  -U --update           Don't format device, just update
'''
LOG = logging.getLogger(__name__)
ISO_LABEL = f'{KIT_NAME_SHORT}_LINUX'
UFD_LABEL = f'{KIT_NAME_SHORT}_UFD'


# Functions
def build_ufd():
  """Build UFD using selected sources."""
  args = docopt(DOCSTRING)
  log.update_log_path(dest_name='build-ufd', timestamp=True)
  try_print = std.TryAndPrint()
  try_print.catch_all = False
  try_print.indent = 2

  # Check if running with root permissions
  if not linux.running_as_root():
    std.print_error('This script is meant to be run as root')
    std.abort()

  # Show header
  std.print_success(KIT_NAME_FULL)
  std.print_warning('UFD Build Tool')
  std.print_warning(' ')

  # Verify selections
  ufd_dev = verify_ufd(args['--ufd-device'])
  sources = verify_sources(args, SOURCES)
  show_selections(args, sources, ufd_dev, SOURCES)
  if not args['--force']:
    confirm_selections(update=args['--update'])

  # Prep UFD
  if not args['--update']:
    std.print_info('Prep UFD')
    try_print.run(
      message='Zeroing first 64MiB...',
      function=zero_device,
      dev_path=ufd_dev,
      )
    try_print.run(
      message='Creating partition table...',
      function=create_table,
      dev_path=ufd_dev,
      use_mbr=args['--use-mbr'],
      )
    try_print.run(
      message='Setting boot flag...',
      function=set_boot_flag,
      dev_path=ufd_dev,
      use_mbr=args['--use-mbr'],
      )
    try_print.run(
      message='Formatting partition...',
      function=format_partition,
      dev_path=ufd_dev,
      label=UFD_LABEL,
      )

  # Mount UFD
  try_print.run(
    message='Mounting UFD...',
    function=linux.mount,
    source=find_first_partition(ufd_dev),
    mount_point='/mnt/UFD',
    read_write=True,
    )

  # Remove Arch folder
  if args['--update']:
    try_print.run(
      message='Removing Linux...',
      function=remove_arch,
      )

  # Copy sources
  std.print_standard(' ')
  std.print_info('Copy Sources')
  for s_label, s_path in sources.items():
    try_print.run(
      message='Copying {}...'.format(s_label),
      function=copy_source,
      source=s_path,
      items=ITEMS[s_label],
      overwrite=True,
      )

  # Update boot entries
  std.print_standard(' ')
  std.print_info('Boot Setup')
  try_print.run(
    message='Updating boot entries...',
    function=update_boot_entries,
    )

  # Install syslinux (to partition)
  try_print.run(
    message='Syslinux (partition)...',
    function=install_syslinux_to_partition,
    partition=find_first_partition(ufd_dev),
    )

  # Unmount UFD
  try_print.run(
    message='Unmounting UFD...',
    function=linux.unmount,
    source_or_mountpoint='/mnt/UFD',
    )

  # Install syslinux (to device)
  try_print.run(
    message='Syslinux (device)...',
    function=install_syslinux_to_dev,
    ufd_dev=ufd_dev,
    use_mbr=args['--use-mbr'],
    )

  # Hide items
  std.print_standard(' ')
  std.print_info('Final Touches')
  try_print.run(
    message='Hiding items...',
    function=hide_items,
    ufd_dev=ufd_dev,
    items=ITEMS_HIDDEN,
    )

  # Done
  std.print_standard('\nDone.')
  if not args['--force']:
    std.pause('Press Enter to exit...')


def confirm_selections(update=False):
  """Ask tech to confirm selections, twice if necessary."""
  if not std.ask('Is the above information correct?'):
    std.abort()

  # Safety check
  if not update:
    std.print_standard(' ')
    std.print_warning('SAFETY CHECK')
    std.print_standard(
      'All data will be DELETED from the disk and partition(s) listed above.')
    std.print_colored(
      ['This is irreversible and will lead to', 'DATA LOSS'],
      [None, 'RED'],
      )
    if not std.ask('Asking again to confirm, is this correct?'):
      std.abort()

  std.print_standard(' ')


def copy_source(source, items, overwrite=False):
  """Copy source items to /mnt/UFD."""
  is_image = source.is_file()

  # Mount source if necessary
  if is_image:
    linux.mount(source, '/mnt/Source')

  # Copy items
  for i_source, i_dest in items:
    i_source = f'{"/mnt/Source" if is_image else source}{i_source}'
    i_dest = f'/mnt/UFD{i_dest}'
    try:
      io.recursive_copy(i_source, i_dest, overwrite=overwrite)
    except FileNotFoundError:
      # Going to assume (hope) that this is fine
      pass

  # Unmount source if necessary
  if is_image:
    linux.unmount('/mnt/Source')


def create_table(dev_path, use_mbr=False):
  """Create GPT or DOS partition table."""
  cmd = [
    'parted', dev_path,
    '--script',
    '--',
    'mklabel', 'msdos' if use_mbr else 'gpt',
    'mkpart', 'primary', 'fat32', '4MiB',
    '-1s' if use_mbr else '-4MiB',
    ]
  run_program(cmd)


def find_first_partition(dev_path):
  """Find path to first partition of dev, returns str.

  NOTE: This assumes the dev was just partitioned with
        a single partition.
  """
  cmd = [
    'lsblk',
    '--list',
    '--noheadings',
    '--output', 'name',
    '--paths',
    dev_path,
    ]

  # Run cmd
  proc = run_program(cmd)
  part_path = proc.stdout.splitlines()[-1].strip()

  # Done
  return part_path


def format_partition(dev_path, label):
  """Format first partition on device FAT32."""
  cmd = [
    'mkfs.vfat',
    '-F', '32',
    '-n', label,
    find_first_partition(dev_path),
    ]
  run_program(cmd)


def get_uuid(path):
  """Get filesystem UUID via findmnt, returns str."""
  cmd = [
    'findmnt',
    '--noheadings',
    '--target', path,
    '--output', 'uuid'
    ]

  # Run findmnt
  proc = run_program(cmd, check=False)

  # Done
  return proc.stdout.strip()


def hide_items(ufd_dev, items):
  """Set FAT32 hidden flag for items."""
  first_partition = find_first_partition(ufd_dev)
  with open('/root/.mtoolsrc', 'w') as _f:
    _f.write(f'drive U: file="{first_partition}"\n')
    _f.write('mtools_skip_check=1\n')

  # Hide items
  for item in items:
    cmd = [f'yes | mattrib +h "U:/{item}"']
    run_program(cmd, check=False, shell=True)


def install_syslinux_to_dev(ufd_dev, use_mbr):
  """Install Syslinux to UFD (dev)."""
  cmd = [
    'dd',
    'bs=440',
    'count=1',
    f'if=/usr/lib/syslinux/bios/{"mbr" if use_mbr else "gptmbr"}.bin',
    f'of={ufd_dev}',
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


def set_boot_flag(dev_path, use_mbr=False):
  """Set modern or legacy boot flag."""
  cmd = [
    'parted', dev_path,
    'set', '1',
    'boot' if use_mbr else 'legacy_boot',
    'on',
    ]
  run_program(cmd)


def remove_arch():
  """Remove arch dir from UFD.

  This ensures a clean installation to the UFD and resets the boot files
  """
  shutil.rmtree(io.case_insensitive_path('/mnt/UFD/arch'))


def show_selections(args, sources, ufd_dev, ufd_sources):
  """Show selections including non-specified options."""

  # Sources
  std.print_info('Sources')
  for label in ufd_sources.keys():
    if label in sources:
      std.print_standard(f'  {label+":":<18} {sources[label]}')
    else:
      std.print_colored(
        [f'  {label+":":<18}', 'Not Specified'],
        [None, 'YELLOW'],
        )
  std.print_standard(' ')

  # Destination
  std.print_info('Destination')
  cmd = [
    'lsblk', '--nodeps', '--noheadings', '--paths',
    '--output', 'NAME,FSTYPE,TRAN,SIZE,VENDOR,MODEL,SERIAL',
    ufd_dev,
    ]
  proc = run_program(cmd, check=False)
  std.print_standard(proc.stdout.strip())
  cmd = [
    'lsblk', '--noheadings', '--paths',
    '--output', 'NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT',
    ufd_dev,
    ]
  proc = run_program(cmd, check=False)
  for line in proc.stdout.splitlines()[1:]:
    std.print_standard(line)

  # Notes
  if args['--update']:
    std.print_warning('Updating kit in-place')
  elif args['--use-mbr']:
    std.print_warning('Formatting using legacy MBR')
  std.print_standard(' ')


def update_boot_entries():
  """Update boot files for UFD usage"""
  configs = []
  uuid = get_uuid('/mnt/UFD')

  # Find config files
  for c_path, c_ext in BOOT_FILES.items():
    try:
      c_path = io.case_insensitive_path(f'/mnt/UFD{c_path}')
    except FileNotFoundError:
      # Ignore and continue to next file
      continue
    for item in os.scandir(c_path):
      if item.name.lower().endswith(c_ext.lower()):
        configs.append(item.path)

  # Use UUID instead of label
  cmd = [
    'sed',
    '--in-place',
    '--regexp-extended',
    f's#archisolabel={ISO_LABEL}#archisodevice=/dev/disk/by-uuid/{uuid}#',
    *configs,
    ]
  run_program(cmd)

  # Uncomment extra entries if present
  for b_path, b_comment in BOOT_ENTRIES.items():
    try:
      io.case_insensitive_path(f'/mnt/UFD{b_path}')
    except (FileNotFoundError, NotADirectoryError):
      # Entry not found, continue to next entry
      continue

    # Entry found, update config files
    cmd = [
      'sed',
      '--in-place',
      f's/#{b_comment}#//',
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
        s_path_obj = io.case_insensitive_path(s_path)
      except FileNotFoundError:
        std.print_error(f'ERROR: {label} not found: {s_path}')
        std.abort()
      if not is_valid_path(s_path_obj, data['Type']):
        std.print_error(f'ERROR: Invalid {label} source: {s_path}')
        std.abort()
      sources[label] = s_path_obj

  return sources


def verify_ufd(dev_path):
  """Check that dev_path is a valid UFD, returns pathlib.Path obj."""
  ufd_dev = None

  try:
    ufd_dev = io.case_insensitive_path(dev_path)
  except FileNotFoundError:
    std.print_error(f'ERROR: UFD device not found: {dev_path}')
    std.abort()

  if not is_valid_path(ufd_dev, 'UFD'):
    std.print_error(f'ERROR: Invalid UFD device: {ufd_dev}')
    std.abort()

  return ufd_dev


def zero_device(dev_path):
  """Zero-out first 64MB of device."""
  cmd = [
    'dd',
    'bs=4M',
    'count=16',
    'if=/dev/zero',
    f'of={dev_path}',
    ]
  run_program(cmd)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
