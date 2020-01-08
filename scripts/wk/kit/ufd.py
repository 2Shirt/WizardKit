"""WizardKit: UFD Functions"""
# vim: sts=2 sw=2 ts=2
# TODO: Replace some lsblk usage with hw_obj?
# TODO: Reduce imports if possible
# TODO: Needs testing

import logging
import os
import shutil

from collections import OrderedDict

from wk import io, std
from wk.cfg.main import KIT_NAME_SHORT
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


def prep_device(dev_path, label, use_mbr=False):
  """Format device in preparation for applying the WizardKit components

  This is done is four steps:
  1. Zero-out first 64MB (this deletes the partition table and/or bootloader)
  2. Create a new partition table (GPT by default, optionally MBR)
  3. Set boot flag
  4. Format partition (FAT32, 4K aligned)
  """
  try_print = std.TryAndPrint()

  # Zero-out first 64MB
  cmd = [
    'dd',
    'bs=4M',
    'count=16',
    'if=/dev/zero',
    f'of={dev_path}',
    ]
  try_print.run(
    message='Zeroing first 64MiB...',
    function=run_program,
    cmd=cmd,
    )

  # Create partition table
  cmd = [
    'parted', dev_path,
    '--script',
    '--',
    'mklabel', 'msdos' if use_mbr else 'gpt',
    '-1s' if use_mbr else '-4MiB',
    ]
  try_print.run(
    message='Creating partition table...',
    function=run_program,
    cmd=cmd,
    )

  # Set boot flag
  cmd = [
    'parted', dev_path,
    'set', '1',
    'boot' if use_mbr else 'legacy_boot',
    'on',
    ]
  try_print.run(
    message='Setting boot flag...',
    function=run_program,
    cmd=cmd,
    )

  # Format partition
  cmd = [
    'mkfs.vfat',
    '-F', '32',
    '-n', label,
    find_first_partition(dev_path),
    ]
  try_print.run(
    message='Formatting partition...',
    function=run_program,
    cmd=cmd,
    )


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
      std.print_standard(f'  {label+":":<18} {sources["label"]}')
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


def update_boot_entries(boot_entries, boot_files, iso_label, ufd_label):
  """Update boot files for UFD usage"""
  configs = []

  # Find config files
  for c_path, c_ext in boot_files.items():
    c_path = io.case_insensitive_path('/mnt/UFD{c_path}')
    for item in os.scandir(c_path):
      if item.name.lower().endswith(c_ext.lower()):
        configs.append(item.path)

  # Update Linux labels
  cmd = [
    'sed',
    '--in-place',
    '--regexp-extended',
    f's/{iso_label}/{ufd_label}/',
    *configs,
    ]
  run_program(cmd)

  # Uncomment extra entries if present
  for b_path, b_comment in boot_entries.items():
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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
