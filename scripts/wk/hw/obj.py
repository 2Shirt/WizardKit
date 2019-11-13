"""WizardKit: Hardware objects (mostly)"""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import platform
import plistlib
import re

from collections import OrderedDict

from wk.cfg.hw import (
  ATTRIBUTE_COLORS,
  KEY_NVME,
  KEY_SMART,
  KNOWN_DISK_ATTRIBUTES,
  KNOWN_DISK_MODELS,
  KNOWN_RAM_VENDOR_IDS,
  REGEX_POWER_ON_TIME,
  )
from wk.exe import get_json_from_command, run_program
from wk.std import bytes_to_string, color_string, sleep, string_to_bytes


# STATIC VARIABLES
LOG = logging.getLogger(__name__)


# Exception Classes
class CriticalHardwareError(RuntimeError):
  """Exception used for critical hardware failures."""

class SMARTNotSupportedError(TypeError):
  """Exception used for disks lacking SMART support."""


# Classes
class BaseObj():
  """Base object for tracking device data."""
  def __init__(self):
    self.tests = OrderedDict()

  def all_tests_passed(self):
    """Check if all tests passed, returns bool."""
    return all([results.passed for results in self.tests.values()])

  def any_test_failed(self):
    """Check if any test failed, returns bool."""
    return any([results.failed for results in self.tests.values()])


class CpuRam(BaseObj):
  """Object for tracking CPU & RAM specific data."""
  def __init__(self):
    super().__init__()
    self.description = 'Unknown'
    self.details = {}
    self.ram_total = 'Unknown'
    self.ram_dimms = []
    self.tests = OrderedDict()

    # Update details
    self.get_cpu_details()
    self.get_ram_details()

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


class Disk(BaseObj):
  """Object for tracking disk specific data."""
  def __init__(self, path):
    super().__init__()
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

  def check_attributes(self, only_blocking=False):
    """Check if any known attributes are failing, returns bool."""
    attributes_ok = True
    known_attributes = get_known_disk_attributes(self.details['model'])
    for attr, value in self.attributes.items():
      # Skip unknown attributes
      if attr not in known_attributes:
        continue

      # Get thresholds
      blocking_attribute = known_attributes[attr].get('Blocking', False)
      err_thresh = known_attributes[attr].get('Error', None)
      max_thresh = known_attributes[attr].get('Maximum', None)
      if not max_thresh:
        max_thresh = float('inf')

      # Skip non-blocking attributes if necessary
      if only_blocking and not blocking_attribute:
        continue

      # Skip informational attributes
      if not err_thresh:
        continue

      # Check attribute
      if err_thresh <= value['raw'] < max_thresh:
        attributes_ok = False

    # Done
    return attributes_ok

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
    known_attributes = get_known_disk_attributes(self.details['model'])
    report = []
    for attr, value in sorted(self.attributes.items()):
      note = ''
      value_color = 'GREEN'

      # Skip attributes not in our list
      if attr not in known_attributes:
        continue

      # Check for attribute note
      note = known_attributes[attr].get('Note', '')

      # ID / Name
      label = f'{attr:>3}'
      if isinstance(attr, int):
        # Assuming SMART, include hex ID and name
        label += f' / {str(hex(attr))[2:].upper():0>2}: {value["name"]}'
      label = f'  {label.replace("_", " "):38}'

      # Value color
      for threshold, color in ATTRIBUTE_COLORS:
        threshold_val = known_attributes[attr].get(threshold, None)
        if threshold_val and value['raw'] >= threshold_val:
          value_color = color
          if threshold == 'Error':
            note = '(failed)'
          elif threshold == 'Maximum':
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
        try:
          self.details[attr] = int(self.details[attr])
        except (TypeError, ValueError):
          LOG.error('Invalid disk %s: %s', attr, self.details[attr])
          self.details[attr] = -1

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

  def get_smart_self_test_details(self):
    """Shorthand to get deeply nested self-test details, returns dict."""
    details = {}
    try:
      details = self.smartctl['ata_smart_data']['self_test']
    except (KeyError, TypeError):
      # Assuming disk lacks SMART support, ignore and return empty dict.
      pass

    # Done
    return details

  def is_4k_aligned(self):
    """Check that all disk partitions are aligned, returns bool."""
    aligned = True
    if platform.system() == 'Darwin':
      aligned = is_4k_aligned_macos(self.details)
    elif platform.system() == 'Linux':
      aligned = is_4k_aligned_linux(self.path, self.details['phy-sec'])
    #TODO: Add checks for other OS

    return aligned

  def safety_checks(self):
    """Run safety checks and raise an exception if necessary."""
    blocking_event_encountered = False
    self.update_smart_details()

    # Attributes
    if not self.check_attributes(only_blocking=True):
      blocking_event_encountered = True
      LOG.error('%s: Blocked for failing attribute(s)', self.path)

    # NVMe status
    # TODO: See https://github.com/2Shirt/WizardKit/issues/130

    # SMART overall assessment
    smart_passed = True
    try:
      smart_passed = self.smartctl['smart_status']['passed']
    except (KeyError, TypeError):
      # Assuming disk doesn't support SMART overall assessment
      pass
    if not smart_passed:
      blocking_event_encountered = True
      msg = 'SMART overall self-assessment: Failed'
      self.add_note(msg, 'RED')
      LOG.error('%s %s', self.path, msg)

    # SMART self-test status
    test_details = self.get_smart_self_test_details()
    if 'remaining_percent' in test_details.get('status', ''):
      blocking_event_encountered = True
      msg = 'SMART self-test in progress'
      self.add_note(msg, 'RED')
      LOG.error('%s %s', self.path, msg)

    # Raise exception if necessary
    if blocking_event_encountered:
      raise CriticalHardwareError(f'Critical error(s) for: {self.path}')

  def run_self_test(self, log_path):
    """Run disk self-test and check if it passed, returns bool.

    NOTE: This function is here to reserve a place for future
          NVMe self-tests announced in NVMe spec v1.3.
    """
    result = self.run_smart_self_test(log_path)
    return result

  def run_smart_self_test(self, log_path):
    """Run SMART self-test and check if it passed, returns bool.

    NOTE: An exception will be raised if the disk lacks SMART support.
    """
    finished = False
    result = None
    started = False
    status_str = 'Starting self-test...'
    test_details = self.get_smart_self_test_details()
    test_minutes = 15

    # Check if disk supports self-tests
    if not test_details:
      raise SMARTNotSupportedError(
        f'SMART self-test not supported for {self.path}')

    # Get real test length
    test_minutes = test_details.get('polling_minutes', {}).get('short', 5)
    test_minutes = int(test_minutes) + 10

    # Start test
    cmd = [
      'sudo',
      'smartctl',
      '--tolerance=normal',
      '--test=short',
      self.path,
      ]
    run_program(cmd, check=False)

    # Monitor progress (in five second intervals)
    for _i in range(int(test_minutes*60/5)):
      sleep(5)

      # Update status
      self.update_smart_details()
      test_details = self.get_smart_self_test_details()

      # Check test progress
      if started:
        status_str = test_details.get('status', {}).get('string', 'Unknown')
        status_str = status_str.capitalize()

        # Update log
        with open(log_path, 'w') as _f:
          _f.write(f'SMART self-test status for {self.path}:\n  {status_str}')

        # Check if finished
        if 'remaining_percent' not in test_details['status']:
          finished = True
          break

      elif 'remaining_percent' in test_details['status']:
        started = True

    # Check result
    if finished:
      result = test_details.get('status', {}).get('passed', False)
    elif started:
      raise TimeoutError(f'SMART self-test timed out for {self.path}')

    # Done
    return result

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


class Test():
  """Object for tracking test specific data."""
  def __init__(self, dev, label):
    self.dev = dev
    self.disabled = False
    self.failed = False
    self.label = label
    self.passed = False
    self.report = []
    self.status = ''

  def set_status(self, status):
    """Update status string."""
    if self.disabled:
      # Don't change status if disabled
      return

    self.status = status


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
    # Invalid / corrupt plist data? return empty dict to avoid crash
    LOG.error('Failed to get diskutil list for %s', path)
    return details

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


def get_known_disk_attributes(model):
  """Get known NVMe/SMART attributes (model specific), returns str."""
  known_attributes = KNOWN_DISK_ATTRIBUTES.copy()

  # Apply model-specific data
  for regex, data in KNOWN_DISK_MODELS.items():
    if re.search(regex, model):
      for attr, thresholds in data.items():
        if attr in known_attributes:
          known_attributes[attr].update(thresholds)
        else:
          known_attributes[attr] = thresholds

  # Done
  return known_attributes


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
      try:
        size = string_to_bytes(size, assume_binary=True)
      except ValueError:
        # Assuming empty module
        size = 0
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
    manufacturer = KNOWN_RAM_VENDOR_IDS.get(
      manufacturer,
      f'Unknown ({manufacturer})')
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


def is_4k_aligned_macos(disk_details):
  """Check partition alignment using diskutil info, returns bool."""
  aligned = True

  # Check partitions
  for part in disk_details.get('children', []):
    offset = part.get('PartitionMapPartitionOffset', 0)
    if not offset:
      # Assuming offset couldn't be found and it defaulted to 0
      # NOTE: Just logging the error, not bailing
      LOG.error('Failed to get partition offset for %s', part['path'])
    aligned = aligned and offset >= 0 and offset % 4096 == 0

  # Done
  return aligned


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
