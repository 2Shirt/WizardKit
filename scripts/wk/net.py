"""WizardKit: Net Functions"""
# vim: sts=2 sw=2 ts=2

import os
import pathlib
import re

import psutil

from wk.exe import get_json_from_command, run_program
from wk.std import PLATFORM, GenericError, show_data

from wk.cfg.net import BACKUP_SERVERS


# REGEX
REGEX_VALID_IP = re.compile(
  r'(10.\d+.\d+.\d+'
  r'|172.(1[6-9]|2\d|3[0-1])'
  r'|192.168.\d+.\d+)',
  re.IGNORECASE)


# Functions
def connected_to_private_network(raise_on_error=False):
  """Check if connected to a private network, returns bool.

  This checks for a valid private IP assigned to this system.

  NOTE: If one isn't found and raise_on_error=True then an exception is raised.
  NOTE 2: If one is found and raise_on_error=True then None is returned.
  """
  connected = False

  # Check IPs
  devs = psutil.net_if_addrs()
  for dev in devs.values():
    for family in dev:
      if REGEX_VALID_IP.search(family.address):
        # Valid IP found
        connected = True
        break
    if connected:
      break

  # No valid IP found
  if not connected and raise_on_error:
    raise GenericError('Not connected to a network')

  # Done
  if raise_on_error:
    connected = None
  return connected


def mount_backup_shares(read_write=False):
  """Mount backup shares using OS specific methods."""
  report = []
  for name, details in BACKUP_SERVERS.items():
    mount_point = None
    mount_str = f'{name} (//{details["Address"]}/{details["Share"]})'

    # Prep mount point
    if PLATFORM in ('Darwin', 'Linux'):
      mount_point = pathlib.Path(f'/Backups/{name}')
      try:
        if not mount_point.exists():
          # Script should be run as user so sudo is required
          run_program(['sudo', 'mkdir', '-p', mount_point])
      except OSError:
        # Assuming permission denied under macOS
        pass
    if mount_point:
      mount_str += f' to {mount_point}'

    # Check if already mounted
    if share_is_mounted(details):
      report.append(f'(Already) Mounted {mount_str}')
      # Skip to next share
      continue

    # Mount share
    proc = mount_network_share(details, mount_point, read_write=read_write)
    if proc.returncode:
      report.append(f'Failed to Mount {mount_str}')
    else:
      report.append(f'Mounted {mount_str}')

  # Done
  return report


def mount_network_share(details, mount_point=None, read_write=False):
  """Mount network share using OS specific methods."""
  cmd = None
  address = details['Address']
  share = details['Share']
  username = details['RO-User']
  password = details['RO-Pass']
  if read_write:
    username = details['RW-User']
    password = details['RW-Pass']

  # Network check
  if not connected_to_private_network():
    raise RuntimeError('Not connected to a network')

  # Build OS-specific command
  if PLATFORM == 'Darwin':
    cmd = [
      'sudo',
      'mount',
      '-t', 'smbfs',
      '-o', f'{"rw" if read_write else "ro"}',
      f'//{username}:{password}@{address}/{share}',
      mount_point,
      ]
  elif PLATFORM == 'Linux':
    cmd = [
      'sudo',
      'mount',
      '-t', 'cifs',
      '-o', (
        f'{"rw" if read_write else "ro"}'
        f',uid={os.getuid()}' # pylint: disable=no-member
        f',gid={os.getgid()}' # pylint: disable=no-member
        f',username={username}'
        f',{"password=" if password else "guest"}{password}'
        ),
      f'//{address}/{share}',
      mount_point
      ]
  elif PLATFORM == 'Windows':
    cmd = ['net', 'use']
    if mount_point:
      cmd.append(f'{mount_point}:')
    cmd.append(f'/user:{username}')
    cmd.append(fr'\\{address}\{share}')
    cmd.append(password)

  # Mount share
  return run_program(cmd, check=False)


def ping(addr='google.com'):
  """Attempt to ping addr."""
  cmd = (
    'ping',
    '-n' if psutil.WINDOWS else '-c',
    '2',
    addr,
    )
  run_program(cmd)


def share_is_mounted(details):
  """Check if dev/share/etc is mounted, returns bool."""
  mounted = False

  if PLATFORM == 'Darwin':
    # Weak and naive text search
    proc = run_program(['mount'], check=False)
    for line in proc.stdout.splitlines():
      if f'{details["Address"]}/{details["Share"]}' in line:
        mounted = True
        break
  elif PLATFORM == 'Linux':
    cmd = [
      'findmnt',
      '--list',
      '--json',
      '--invert',
      '--types', (
        'autofs,binfmt_misc,bpf,cgroup,cgroup2,configfs,debugfs,devpts,'
        'devtmpfs,hugetlbfs,mqueue,proc,pstore,securityfs,sysfs,tmpfs'
        ),
      '--output', 'SOURCE',
      ]
    mount_data = get_json_from_command(cmd)
    for row in mount_data.get('filesystems', []):
      if row['source'] == f'//{details["Address"]}/{details["Share"]}':
        mounted = True
        break
  #elif PLATFORM == 'Windows':

  # Done
  return mounted


def show_valid_addresses():
  """Show all valid private IP addresses assigned to the system."""
  devs = psutil.net_if_addrs()
  for dev, families in sorted(devs.items()):
    for family in families:
      if REGEX_VALID_IP.search(family.address):
        # Valid IP found
        show_data(message=dev, data=family.address)


def speedtest():
  """Run a network speedtest using speedtest-cli."""
  cmd = ['speedtest-cli', '--simple']
  proc = run_program(cmd, check=False)
  output = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
  output = [line.split() for line in output]
  output = [(a, float(b), c) for a, b, c in output]
  return [f'{a:<10}{b:6.2f} {c}' for a, b, c in output]


def unmount_backup_shares():
  """Unmount backup shares."""
  report = []
  for name, details in BACKUP_SERVERS.items():
    kwargs = {}
    source_str = f'{name} (//{details["Address"]}/{details["Share"]})'

    # Check if mounted
    if not share_is_mounted(details):
      report.append(f'Not mounted {source_str}')
      continue

    # Build OS specific kwargs
    if PLATFORM in ('Darwin', 'Linux'):
      kwargs['mount_point'] = f'/Backups/{name}'
    elif PLATFORM == 'Windows':
      kwargs['details'] = details

    # Unmount and add to report
    proc = unmount_network_share(**kwargs)
    if proc.returncode:
      report.append(f'Failed to unmount {source_str}')
    else:
      report.append(f'Unmounted {source_str}')

  # Done
  return report


def unmount_network_share(details=None, mount_point=None):
  """Unmount network share"""
  cmd = []

  # Build OS specific command
  if PLATFORM in ('Darwin', 'Linux'):
    cmd = ['sudo', 'umount', mount_point]
  elif PLATFORM == 'Windows':
    cmd = ['net', 'use']
    if mount_point:
      cmd.append(f'{mount_point}:')
    elif details:
      cmd.append(fr'\\{details["Address"]}\{details["Share"]}')
    cmd.append('/delete')

  # Unmount share
  return run_program(cmd, check=False)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
