# Wizard Kit: Functions - Network

import os
import shutil
import sys

from functions.common import *


# REGEX
REGEX_VALID_IP = re.compile(
  r'(10.\d+.\d+.\d+'
  r'|172.(1[6-9]|2\d|3[0-1])'
  r'|192.168.\d+.\d+)',
  re.IGNORECASE)


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
  result = run_program(['speedtest-cli', '--simple'])
  output = [line.strip() for line in result.stdout.decode().splitlines()
    if line.strip()]
  output = [line.split() for line in output]
  output = [(a, float(b), c) for a, b, c in output]
  return ['{:10}{:6.2f} {}'.format(*line) for line in output]


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
