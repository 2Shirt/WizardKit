"""WizardKit: Net Functions"""
# vim: sts=2 sw=2 ts=2

import re

import psutil

from wk.exe import run_program
from wk.std import show_data

# REGEX
REGEX_VALID_IP = re.compile(
  r'(10.\d+.\d+.\d+'
  r'|172.(1[6-9]|2\d|3[0-1])'
  r'|192.168.\d+.\d+)',
  re.IGNORECASE)


# Functions
def is_connected():
  """Check for a valid private IP."""
  devs = psutil.net_if_addrs()
  for dev in devs.values():
    for family in dev:
      if REGEX_VALID_IP.search(family.address):
        # Valid IP found
        return True
  # Else
  return False


def ping(addr='google.com'):
  """Attempt to ping addr."""
  cmd = (
    'ping',
    '-n' if psutil.WINDOWS else '-c',
    '2',
    addr,
    )
  run_program(cmd)


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
  output = [line.strip() for line in proc.stdout.splitlines()]
  output = [line.split() for line in output]
  output = [(a, float(b), c) for a, b, c in output]
  return [f'{a:<10}{b:6.2f} {c}' for a, b, c in output]


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
