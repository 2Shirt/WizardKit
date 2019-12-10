"""WizardKit: Net Functions"""
# vim: sts=2 sw=2 ts=2

import os
import pathlib
import platform
import re

import psutil

from wk.exe import get_json_from_command, run_program
from wk.std import GenericError, show_data

from wk.cfg.net import BACKUP_SERVERS


# REGEX
REGEX_VALID_IP = re.compile(
  r'(10.\d+.\d+.\d+'
  r'|172.(1[6-9]|2\d|3[0-1])'
  r'|192.168.\d+.\d+)',
  re.IGNORECASE)


# Functions
def connected_to_private_network():
  """Check if connected to a private network.

  This checks for a valid private IP assigned to this system.
  If one isn't found then an exception is raised.
  """
  devs = psutil.net_if_addrs()
  for dev in devs.values():
    for family in dev:
      if REGEX_VALID_IP.search(family.address):
        # Valid IP found
        return

  # No valid IP found
  raise GenericError('Not connected to a network')


def mount_backup_shares(read_write=False):
  """Mount backup shares using OS specific methods."""
  report = []
  for name, details in BACKUP_SERVERS.items():
    mount_point = None
    mount_str = f'//{name}/{details["Share"]}'

    # Prep mount point
    if platform.system() in ('Darwin', 'Linux'):
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

  # Build OS-specific command
  if platform.system() == 'Darwin':
    cmd = [
      'sudo',
      'mount',
      '-t', 'smbfs',
      '-o', f'{"rw" if read_write else "ro"}',
      f'//{username}:{password}@{address}/{share}',
      mount_point,
      ]
  elif platform.system() == 'Linux':
    cmd = [
      'sudo',
      'mount',
      '-t', 'cifs',
      '-o', (
        f'{"rw" if read_write else "ro"}'
        f',uid={os.getuid()}'
        f',gid={os.getgid()}'
        f',username={username}'
        f',{"password=" if password else "guest"}{password}'
        ),
      f'//{address}/{share}',
      mount_point
      ]
  elif platform.system() == 'Windows':
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

  if platform.system() == 'Darwin':
    # Weak and naive text search
    proc = run_program(['mount'], check=False)
    for line in proc.stdout.splitlines():
      if f'{details["Address"]}/{details["Share"]}' in line:
        mounted = True
        break
  elif platform.system() == 'Linux':
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
  #TODO: Check mount status under Windows
  #elif platform.system() == 'Windows':

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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
