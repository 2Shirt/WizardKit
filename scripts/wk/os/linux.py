"""WizardKit: Linux Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import pathlib
import re
import subprocess

from wk import std
from wk.exe import popen_program, run_program
from wk.hw.obj import Disk


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
UUID_CORESTORAGE = '53746f72-6167-11aa-aa11-00306543ecac'


# Functions
def get_user_home(user):
  """Get path to user's home dir, returns pathlib.Path obj."""
  home = None

  # Get path from user details
  cmd = ['getent', 'passwd', user]
  proc = run_program(cmd, check=False)
  try:
    home = proc.stdout.split(':')[5]
  except IndexError:
    # Try using environment variable
    home = os.environ.get('HOME')

  # Raise exception if necessary
  if not home:
    raise RuntimeError(f'Failed to find home for: {user}')

  # Done
  return pathlib.Path(home)


def get_user_name():
  """Get real user name, returns str."""
  user = None

  # Query environment
  user = os.environ.get('SUDO_USER')
  if not user:
    user = os.environ.get('USER')

  # Raise exception if necessary
  if not user:
    raise RuntimeError('Failed to determine user')

  # Done
  return user


def make_temp_file():
  """Make temporary file, returns pathlib.Path() obj."""
  proc = run_program(['mktemp'], check=False)
  return pathlib.Path(proc.stdout.strip())


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


def running_as_root():
  """Check if running with effective UID of 0, returns bool."""
  return os.geteuid() == 0


def scan_corestorage_container(container, timeout=300):
  """Scan CoreStorage container for inner volumes, returns list."""
  # TODO: Test Scanning CoreStorage containers
  detected_volumes = {}
  inner_volumes = []
  log_path = make_temp_file()

  # Run scan via TestDisk
  cmd = [
    'sudo', 'testdisk',
    '/logname', log_path,
    '/debug',
    '/log',
    '/cmd', container.path, 'partition_none,analyze',
    ]
  proc = popen_program(cmd)
  try:
    proc.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
    # Failed to find any volumes, stop scan
    run_program(['sudo', 'kill', proc.pid], check=False)

  # Check results
  if proc.returncode == 0 and log_path.exists():
    results = log_path.read_text(encoding='utf-8', errors='ignore')
    for line in results.splitlines():
      line = line.lower().strip()
      match = re.match(r'^.*echo "([^"]+)" . dmsetup create test(\d)$', line)
      if match:
        cs_name = f'CoreStorage_{container.path.name}_{match.group(2)}'
        detected_volumes[cs_name] = match.group(1)

  # Create mapper device(s) if necessary
  for name, cmd in detected_volumes.items():
    cmd_file = make_temp_file()
    cmd_file.write_text(cmd)
    proc = run_program(
      cmd=['sudo', 'dmsetup', 'create', name, cmd_file],
      check=False,
      )
    if proc.returncode == 0:
      inner_volumes.append(Disk(f'/dev/mapper/{name}'))

  # Done
  return inner_volumes


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
