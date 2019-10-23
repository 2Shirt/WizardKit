"""WizardKit: Objects."""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import re

from collections import OrderedDict

from wk.exe import get_json_from_command, run_program
from wk.std import bytes_to_string, color_string, string_to_bytes

# STATIC VARIABLES
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'
LOG = logging.getLogger(__name__)
REGEX_POWER_ON_TIME = re.compile(
  r'^(\d+)([Hh].*|\s+\(\d+\s+\d+\s+\d+\).*)'
  )

# Classes
class CpuRam():
  """Object for tracking CPU & RAM specific data."""
  def __init__(self):
    self.lscpu = {}
    self.tests = OrderedDict()
    self.get_cpu_details()
    self.get_ram_details()
    self.name = self.lscpu.get('Model name', 'Unknown CPU')
    self.description = self.name

  def get_cpu_details(self):
    """Get CPU details from lscpu."""
    cmd = ['lscpu', '--json']
    json_data = get_json_from_command(cmd)
    for line in json_data.get('lscpu', [{}]):
      _field = line.get('field', '').replace(':', '')
      _data = line.get('data', '')
      if not (_field or _data):
        # Skip
        continue
      self.lscpu[_field] = _data

  def get_ram_details(self):
    """Get RAM details from dmidecode."""
    cmd = ['sudo', 'dmidecode', '--type', 'memory']
    manufacturer = 'UNKNOWN'
    details = {'Total': 0}
    size = 0

    # Get DMI data
    proc = run_program(cmd)
    dmi_data = proc.stdout.splitlines()

    # Parse data
    for line in dmi_data:
      line = line.strip()
      if line == 'Memory Device':
        # Reset vars
        manufacturer = 'UNKNOWN'
        size = 0
      elif line.startswith('Size:'):
        size = line.replace('Size: ', '')
        size = string_to_bytes(size, assume_binary=True)
      elif line.startswith('Manufacturer:'):
        manufacturer = line.replace('Manufacturer: ', '')
        if size <= 0:
          # Skip non-populated slots
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
    report.append(f'  {self.name}')

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
    self.description = 'UNKNOWN'
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
      size_str = bytes_to_string(self.lsblk['size'], use_binary=False),
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
        name = str(attribute.get('name', 'UNKNOWN')).replace('_', ' ').title()
        raw = int(attribute.get('raw', {}).get('value', -1))
        raw_str = attribute.get('raw', {}).get('string', 'UNKNOWN')

        # Fix power-on time
        match = REGEX_POWER_ON_TIME.match(raw_str)
        if _id == 9 and match:
          raw = int(match.group(1))

        # Add to dict
        self.attributes[_id] = {
          'name': name, 'raw': raw, 'raw_str': raw_str}


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
