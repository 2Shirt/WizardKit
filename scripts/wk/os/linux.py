"""WizardKit: Linux Functions"""
# vim: sts=2 sw=2 ts=2

import logging

from wk import std
from wk.exe import run_program
from wk.hw.obj import Disk


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
UUID_CORESTORAGE = '53746f72-6167-11aa-aa11-00306543ecac'


# Functions
def mount_volumes(device_path=None, read_write=False, scan_corestorage=False):
  """Mount all detected volumes, returns list.

  NOTE: If device_path is specified then only volumes
        under that path will be mounted.
  """
  report = []
  volumes = []
  containers = []

  # Get list of volumes
  cmd = [
    'lsblk',
    '--list',
    '--noheadings',
    '--output=name',
    '--paths',
    ]
  if device_path:
    cmd.append(device_path)
  proc = run_program(cmd, check=False)
  for line in sorted(proc.stdout.splitlines()):
    volumes.append(Disk(line.strip()))

  # Get list of CoreStorage containers
  containers = [
    vol for vol in volumes if vol.details.get('parttype', '') == UUID_CORESTORAGE
    ]

  # Scan CoreStorage containers
  if scan_corestorage:
    if containers:
      std.print_warning(
        f'Detected CoreStorage container{"s" if len(containers) > 1 else ""}',
        )
      std.print_standard('Scanning for inner volume(s)...')
    for container in containers:
      volumes.extend(scan_corestorage_container(container))

  # Mount volumes
  for vol in volumes:
    already_mounted = vol.details.get('mountpoint', '')
    result = f'{vol.details["name"].replace("/dev/mapper/", ""):<20}'

    # Parent devices
    if vol.details.get('children', False):
      if vol.details.get('fstype', ''):
        result += vol.details['fstype']
        if vol.details.get('label', ''):
          result += f' "{vol.details["label"]}"'
        report.append(std.color_string(result, 'BLUE'))
      continue

    # Attempt to mount volume
    if not already_mounted:
      cmd = [
        'udevil',
        'mount',
        '-o', 'rw' if read_write else 'ro',
        vol.path,
        ]
      proc = run_program(cmd, check=False)
      if proc.returncode:
        result += 'Failed to mount'
        report.append(std.color_string(result, 'RED'))
        continue

    # Add size to result
    vol.get_details()
    vol.details['fsused'] = vol.details.get('fsused', -1)
    vol.details['fsavail'] = vol.details.get('fsavail', -1)
    result += f'{"Mounted on "+vol.details.get("mountpoint", "?"):<40}'
    result = (
      f'{result} ({vol.details.get("fstype", "Unknown FS")+",":<5} '
      f'{std.bytes_to_string(vol.details["fsused"], decimals=1):>9} used, '
      f'{std.bytes_to_string(vol.details["fsavail"], decimals=1):>9} free)'
      )
    report.append(
      std.color_string(
        result,
        'YELLOW' if already_mounted else None,
        ),
      )

  # Done
  return report


def scan_corestorage_container(container, timeout=300):
  """Scan CoreStorage container for inner volumes, returns list."""
  inner_volumes = []

  #TODO: Add testdisk logic to scan CoreStorage
  if container or timeout:
    pass

  # Done
  return inner_volumes


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
