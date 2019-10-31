"""WizardKit: Hardware objects (mostly)"""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import platform
import plistlib
import re

from collections import OrderedDict

from wk.cfg.hw import ATTRIBUTES, ATTRIBUTE_COLORS
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

  def generate_report(self):
    """Generate CPU & RAM report, returns list."""
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
    self.details = {}
    self.notes = []
    self.path = pathlib.Path(path).resolve()
    self.smartctl = {}
    self.tests = OrderedDict()

    # Update details
    self.get_details()
    self.enable_smart()
    self.update_smart_details()
    if not self.is_4k_aligned():
      self.add_note('One or more partitions are not 4K aligned', 'YELLOW')

  def add_note(self, note, color=None):
    """Add note that will be included in the disk report."""
    if color:
      note = color_string(note, color)
    if note not in self.notes:
      self.notes.append(note)
      self.notes.sort()

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

  def generate_attribute_report(self):
    """Generate attribute report, returns list."""
    report = []
    for attr, value in sorted(self.attributes.items()):
      note = ''
      value_color = 'GREEN'

      # Skip attributes not in our list
      if attr not in ATTRIBUTES:
        continue

      # ID / Name
      label = f'{attr:>3}'
      if isinstance(attr, int):
        # Assuming SMART, include hex ID and name
        label += f' / {str(hex(attr))[2:].upper():0>2}: {value["name"]}'
      label = f'  {label.replace("_", " "):38}'

      # Value color
      for threshold, color in ATTRIBUTE_COLORS:
        threshold_val = ATTRIBUTES.get(attr, {}).get(threshold, float('inf'))
        if threshold_val and value['raw'] >= threshold_val:
          value_color = color
          if threshold == 'Maximum':
            note = '(invalid?)'

      # 199/C7 warning
      if str(attr) == '199' and value['raw'] > 0:
        note = '(bad cable?)'

      # Build colored string and append to report
      line = color_string(
        [label, value['raw_str'], note],
        [None, value_color, 'YELLOW'],
        )
      report.append(line)

    # Done
    return report


  def generate_report(self):
    """Generate Disk report, returns list."""
    report = []
    report.append(color_string(f'Device ({self.path.name})', 'BLUE'))
    report.append(f'  {self.description}')

    # Attributes
    if self.attributes:
      report.append(color_string('Attributes', 'BLUE'))
      report.extend(self.generate_attribute_report())

    # Notes
    if self.notes:
      report.append(color_string('Notes', 'BLUE'))
    for note in self.notes:
      report.append(f'  {note}')

    # Tests
    for test in self.tests.values():
      report.extend(test.report)

    return report

  def get_details(self):
    """Get disk details using OS specific methods.

    Required details default to generic descriptions
    and are converted to the correct type.
    """
    if platform.system() == 'Darwin':
      self.details = get_disk_details_macos(self.path)
    elif platform.system() == 'Linux':
      self.details = get_disk_details_linux(self.path)

    # Set necessary details
    self.details['bus'] = self.details.get('bus', '???')
    self.details['bus'] = self.details['bus'].upper().replace('NVME', 'NVMe')
    self.details['model'] = self.details.get('model', 'Unknown Model')
    self.details['name'] = self.details.get('name', self.path)
    self.details['phy-sec'] = self.details.get('phy-sec', 512)
    self.details['serial'] = self.details.get('serial', 'Unknown Serial')
    self.details['size'] = self.details.get('size', -1)
    self.details['ssd'] = self.details.get('ssd', False)

    # Ensure certain attributes types
    for attr in ['bus', 'model', 'name', 'serial']:
      if not isinstance(self.details[attr], str):
        self.details[attr] = str(self.details[attr])
    for attr in ['phy-sec', 'size']:
      if not isinstance(self.details[attr], int):
        self.details[attr] = int(self.details[attr])

    # Set description
    self.description = '{size_str} ({bus}) {model} {serial}'.format(
      size_str=bytes_to_string(self.details['size'], use_binary=False),
      **self.details,
      )

  def get_labels(self):
    """Build list of labels for this disk, returns list."""
    labels = []

    # Add all labels from lsblk
    for disk in [self.details, *self.details.get('children', [])]:
      labels.append(disk.get('label', ''))
      labels.append(disk.get('partlabel', ''))

    # Remove empty labels
    labels = [str(label) for label in labels if label]

    # Done
    return labels

  def is_4k_aligned(self):
    """Check that all disk partitions are aligned, returns bool."""
    aligned = True
    if platform.system() == 'Linux':
      aligned = is_4k_aligned_linux(self.path, self.details['phy-sec'])
    #TODO: Add checks for other OS

    return aligned

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

    # Add note if necessary
    if not self.attributes:
      self.add_note('No NVMe or SMART data available', 'YELLOW')


# Functions
def get_disk_details_linux(path):
  """Get disk details using lsblk, returns dict."""
  cmd = ['lsblk', '--bytes', '--json', '--output-all', '--paths', path]
  json_data = get_json_from_command(cmd, check=False)
  details = json_data.get('blockdevices', [{}])[0]
  details['bus'] = details.pop('tran', '???')
  details['ssd'] = not details.pop('rota', True)
  return details


def get_disk_details_macos(path):
  """Get disk details using diskutil, returns dict."""
  details = {}

  # Get "list" details
  cmd = ['diskutil', 'list', '-plist', path]
  proc = run_program(cmd, check=False, encoding=None, errors=None)
  try:
    plist_data = plistlib.loads(proc.stdout)
  except (TypeError, ValueError):
    LOG.error('Failed to get diskutil list for %s', path)
    # TODO: Figure this out
    return details #Bail

  # Parse "list" details
  details = plist_data.get('AllDisksAndPartitions', [{}])[0]
  details['children'] = details.pop('Partitions', [])
  details['path'] = path
  for child in details['children']:
    child['path'] = path.with_name(child.get('DeviceIdentifier', 'null'))

  # Get "info" details
  for dev in [details, *details['children']]:
    cmd = ['diskutil', 'info', '-plist', dev['path']]
    proc = run_program(cmd, check=False, encoding=None, errors=None)
    try:
      plist_data = plistlib.loads(proc.stdout)
    except (TypeError, ValueError):
      LOG.error('Failed to get diskutil info for %s', path)
      continue #Skip

    # Parse "info" details
    dev.update(plist_data)
    dev['bus'] = dev.pop('BusProtocol', '???')
    dev['fstype'] = dev.pop('FilesystemType', '')
    dev['label'] = dev.pop('VolumeName', '')
    dev['model'] = dev.pop('MediaName', 'Unknown')
    dev['mountpoint'] = dev.pop('MountPoint', '')
    dev['phy-sec'] = dev.pop('DeviceBlockSize', 512)
    dev['serial'] = get_disk_serial_macos(dev['path'])
    dev['size'] = dev.pop('Size', -1)
    dev['ssd'] = dev.pop('SolidState', False)
    dev['vendor'] = ''
    if not dev.get('WholeDisk', True):
      dev['parent'] = dev.pop('ParentWholeDisk', None)

  # Done
  return details


def get_disk_serial_macos(path):
  """Get disk serial using system_profiler, returns str."""
  serial = 'Unknown Serial'
  # TODO: Make it real
  str(path)
  return serial


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


def is_4k_aligned_linux(dev_path, physical_sector_size):
  """Check partition alignment using lsblk, returns bool."""
  aligned = True
  cmd = [
    'sudo',
    'sfdisk',
    '--json',
    dev_path,
    ]

  # Get partition details
  json_data = get_json_from_command(cmd)

  # Check partitions
  for part in json_data.get('partitiontable', {}).get('partitions', []):
    offset = physical_sector_size * part.get('start', -1)
    aligned = aligned and offset >= 0 and offset % 4096 == 0

  # Done
  return aligned


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
