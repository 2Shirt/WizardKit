"""WizardKit: Objects."""
# vim: sts=2 sw=2 ts=2

import pathlib

from collections import OrderedDict

from wk.exe import get_json_from_command, run_program
from wk.std import bytes_to_string, color_string, string_to_bytes

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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
