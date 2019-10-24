"""WizardKit: Objects."""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import platform
import plistlib
import re

from collections import OrderedDict

from wk.exe import get_json_from_command, run_program
from wk.std import bytes_to_string, color_string, string_to_bytes

# STATIC VARIABLES
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'
KNOWN_RAM_VENDOR_IDS = {
  # https://github.com/hewigovens/hewigovens.github.com/wiki/Memory-vendor-code
  '0x014F': 'Transcend',
  '0x2C00': 'Micron',
  '0x802C': 'Micron',
  '0x80AD': 'Hynix',
  '0x80CE': 'Samsung',
  '0xAD00': 'Hynix',
  '0xCE00': 'Samsung',
  }
LOG = logging.getLogger(__name__)
REGEX_POWER_ON_TIME = re.compile(
  r'^(\d+)([Hh].*|\s+\(\d+\s+\d+\s+\d+\).*)'
  )

# Classes
class CpuRam():
  """Object for tracking CPU & RAM specific data."""
  def __init__(self):
    self.description = 'Unknown'
    self.details = {}
    self.ram_total = 'Unknown'
    self.ram_dimms = []
    self.tests = OrderedDict()

    # Update details
    self.get_cpu_details()
    self.get_ram_details()

  def get_cpu_details(self):
    """Get CPU details using OS specific methods."""
    if platform.system() == 'Darwin':
      cmd = 'sysctl -n machdep.cpu.brand_string'.split()
      proc = run_program(cmd, check=False)
      self.description = re.sub(r'\s+', ' ', proc.stdout.strip())
    elif platform.system() == 'Linux':
      cmd = ['lscpu', '--json']
      json_data = get_json_from_command(cmd)
      for line in json_data.get('lscpu', [{}]):
        _field = line.get('field', '').replace(':', '')
        _data = line.get('data', '')
        if not (_field or _data):
          # Skip
          continue
        self.details[_field] = _data

      self.description = self.details.get('Model name', '')

    # Replace empty description
    if not self.description:
      self.description = 'Unknown CPU'

  def get_ram_details(self):
    """Get RAM details using OS specific methods."""
    if platform.system() == 'Darwin':
      dimm_list = get_ram_list_macos()
    elif platform.system() == 'Linux':
      dimm_list = get_ram_list_linux()

    details = {'Total': 0}
    for dimm_details in dimm_list:
      size, manufacturer = dimm_details
      if size <= 0:
        # Skip empty DIMMs
        continue
      description = f'{bytes_to_string(size)} {manufacturer}'
      details['Total'] += size
      if description in details:
        details[description] += 1
      else:
        details[description] = 1

    # Save details
    self.ram_total = bytes_to_string(details.pop('Total', 0))
    self.ram_dimms = [
      f'{count}x {desc}' for desc, count in sorted(details.items())
      ]

  def generate_cpu_report(self):
    """Generate CPU report with data from all tests."""
    report = []
    report.append(color_string('Device', 'BLUE'))
    report.append(f'  {self.description}')

    # Include RAM details
    report.append(color_string('RAM', 'BLUE'))
    report.append(f'  {self.ram_total} ({", ".join(self.ram_dimms)})')

    # Tests
    for test in self.tests.values():
      report.extend(test.report)

    return report


class Disk():
  """Object for tracking disk specific data."""
  def __init__(self, path):
    self.attributes = {}
    self.description = 'Unknown'
    self.lsblk = {}
    self.nvme_smart_notes = {}
    self.path = pathlib.Path(path).resolve()
    self.smartctl = {}
    self.tests = OrderedDict()

    # Update details
    self.get_details()
    self.enable_smart()
    self.update_smart_details()

  def enable_smart(self):
    """Try enabling SMART for this disk."""
    cmd = [
      'sudo',
      'smartctl',
      '--tolerance=permissive',
      '--smart=on',
      self.path,
      ]
    run_program(cmd, check=False)

  def get_details(self):
    """Get details via lsblk.

    Required details default to generic descriptions and
    are converted to the correct type.
    """
    cmd = ['lsblk', '--bytes', '--json', '--output-all', '--paths', self.path]
    json_data = get_json_from_command(cmd)
    self.lsblk = json_data.get('blockdevices', [{}])[0]

    # Set necessary details
    self.lsblk['model'] = self.lsblk.get('model', 'Unknown Model')
    self.lsblk['name'] = self.lsblk.get('name', self.path)
    self.lsblk['log-sec'] = self.lsblk.get('log-sec', 512)
    self.lsblk['phy-sec'] = self.lsblk.get('phy-sec', 512)
    self.lsblk['rota'] = self.lsblk.get('rota', True)
    self.lsblk['serial'] = self.lsblk.get('serial', 'Unknown Serial')
    self.lsblk['size'] = self.lsblk.get('size', -1)
    self.lsblk['tran'] = self.lsblk.get('tran', '???')
    self.lsblk['tran'] = self.lsblk['tran'].upper().replace('NVME', 'NVMe')

    # Ensure certain attributes types
    for attr in ['model', 'name', 'serial', 'tran']:
      if not isinstance(self.lsblk[attr], str):
        self.lsblk[attr] = str(self.lsblk[attr])
    for attr in ['log-sec', 'phy-sec', 'size']:
      if not isinstance(self.lsblk[attr], int):
        self.lsblk[attr] = int(self.lsblk[attr])

    # Set description
    self.description = '{size_str} ({tran}) {model} {serial}'.format(
      size_str=bytes_to_string(self.lsblk['size'], use_binary=False),
      **self.lsblk,
      )

  def get_labels(self):
    """Build list of labels for this disk, returns list."""
    labels = []

    # Add all labels from lsblk
    for disk in [self.lsblk, *self.lsblk.get('children', [])]:
      labels.append(disk.get('label', ''))
      labels.append(disk.get('partlabel', ''))

    # Remove empty labels
    labels = [str(label) for label in labels if label]

    # Done
    return labels

  def update_smart_details(self):
    """Update SMART details via smartctl."""
    self.attributes = {}
    cmd = [
      'sudo',
      'smartctl',
      '--tolerance=verypermissive',
      '--all',
      '--json',
      self.path,
      ]
    self.smartctl = get_json_from_command(cmd, check=False)

    # Check for attributes
    if KEY_NVME in self.smartctl:
      for name, value in self.smartctl[KEY_NVME].items():
        try:
          self.attributes[name] = {
            'name': name,
            'raw': int(value),
            'raw_str': str(value),
            }
        except ValueError:
          # Ignoring invalid attribute
          LOG.error('Invalid NVMe attribute: %s %s', name, value)
    elif KEY_SMART in self.smartctl:
      for attribute in self.smartctl[KEY_SMART].get('table', {}):
        try:
          _id = int(attribute['id'])
        except (KeyError, ValueError):
          # Ignoring invalid attribute
          LOG.error('Invalid SMART attribute: %s', attribute)
          continue
        name = str(attribute.get('name', 'Unknown')).replace('_', ' ').title()
        raw = int(attribute.get('raw', {}).get('value', -1))
        raw_str = attribute.get('raw', {}).get('string', 'Unknown')

        # Fix power-on time
        match = REGEX_POWER_ON_TIME.match(raw_str)
        if _id == 9 and match:
          raw = int(match.group(1))

        # Add to dict
        self.attributes[_id] = {
          'name': name, 'raw': raw, 'raw_str': raw_str}


# Functions
def get_ram_list_linux():
  """Get RAM list using dmidecode."""
  cmd = ['sudo', 'dmidecode', '--type', 'memory']
  dimm_list = []
  manufacturer = 'Unknown'
  size = 0

  # Get DMI data
  proc = run_program(cmd)
  dmi_data = proc.stdout.splitlines()

  # Parse data
  for line in dmi_data:
    line = line.strip()
    if line == 'Memory Device':
      # Reset vars
      manufacturer = 'Unknown'
      size = 0
    elif line.startswith('Size:'):
      size = line.replace('Size: ', '')
      size = string_to_bytes(size, assume_binary=True)
    elif line.startswith('Manufacturer:'):
      manufacturer = line.replace('Manufacturer: ', '')
      dimm_list.append([size, manufacturer])

  # Save details
  return dimm_list

def get_ram_list_macos():
  """Get RAM list using system_profiler."""
  dimm_list = []

  # Get and parse plist data
  cmd = [
    'system_profiler',
    '-xml',
    'SPMemoryDataType',
    ]
  proc = run_program(cmd, check=False, encoding=None, errors=None)
  try:
    plist_data = plistlib.loads(proc.stdout)
  except (TypeError, ValueError):
    # Ignore and return an empty list
    return dimm_list

  # Check DIMM data
  dimm_details = plist_data[0].get('_items', [{}])[0].get('_items', [])
  for dimm in dimm_details:
    manufacturer = dimm.get('dimm_manufacturer', None)
    manufacturer = KNOWN_RAM_VENDOR_IDS.get(manufacturer, 'Unknown')
    size = dimm.get('dimm_size', '0 GB')
    try:
      size = string_to_bytes(size, assume_binary=True)
    except ValueError:
      # Empty DIMM?
      LOG.error('Invalid DIMM size: %s', size)
      continue
    dimm_list.append([size, manufacturer])

  # Save details
  return dimm_list


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
