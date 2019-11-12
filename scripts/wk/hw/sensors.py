"""WizardKit: Hardware sensors"""
# vim: sts=2 sw=2 ts=2

import json
import logging
import platform
import re

from subprocess import CalledProcessError

from wk.cfg.hw import SMC_IDS, TEMP_COLORS
from wk.exe import run_program
from wk.std import color_string


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
LM_SENSORS_CPU_REGEX = re.compile(r'(core|k\d+)temp', re.IGNORECASE)
SMC_REGEX = re.compile(
  r'^\s*(?P<ID>\w{4})'
  r'\s+\[(?P<Type>.*)\]'
  r'\s+(?P<Value>.*?)'
  r'\s*\(bytes (?P<Bytes>.*)\)$'
  )


# Error Classes
class ThermalLimitReachedError(RuntimeError):
  """Raised when the thermal threshold is reached."""


# Classes
class Sensors():
  """Class for holding sensor specific data."""
  def __init__(self):
    self.data = get_sensor_data()

  def clear_temps(self):
    """Clear saved temps but keep structure"""
    for adapters in self.data.values():
      for sources in adapters.values():
        for source_data in sources.values():
          source_data['Temps'] = []

  def generate_report(self, *temp_labels, colored=True, only_cpu=False):
    """Generate report based on given temp_labels, returns list."""
    report = []

    for section, adapters in sorted(self.data.items()):
      if only_cpu and not section.startswith('CPU'):
        continue

    # Ugly section
      for adapter, sources in sorted(adapters.items()):
        report.append(fix_sensor_name(adapter))
        for source, source_data in sorted(sources.items()):
          line = f'{fix_sensor_name(source):18}  '
          for label in temp_labels:
            if label != 'Current':
              line += f' {label.lower()}: '
            line += get_temp_str(
              source_data.get(label, '???'),
              colored=colored,
              )
          report.append(line)
        if not only_cpu:
          report.append('')

    # Handle empty reports
    if not report:
      report = [
        color_string('WARNING: No sensors found', 'YELLOW'),
        '',
        'Please monitor temps manually',
        ]

    # Done
    return report


# Functions
def fix_sensor_name(name):
  """Cleanup sensor name, returns str."""
  name = re.sub(r'^(\w+)-(\w+)-(\w+)', r'\1 (\2 \3)', name, re.IGNORECASE)
  name = name.title()
  name = name.replace('Coretemp', 'CoreTemp')
  name = name.replace('Acpi', 'ACPI')
  name = name.replace('ACPItz', 'ACPI TZ')
  name = name.replace('Isa ', 'ISA ')
  name = name.replace('Pci ', 'PCI ')
  name = name.replace('Id ', 'ID ')
  name = re.sub(r'(\D+)(\d+)', r'\1 \2', name, re.IGNORECASE)
  name = re.sub(r'^K (\d+)Temp', r'AMD K\1 Temps', name, re.IGNORECASE)
  name = re.sub(r'T(ctl|die)', r'CPU (T\1)', name, re.IGNORECASE)
  return name


def get_lm_sensor_data():
  """Get sensor data via lm_sensors, returns dict."""
  raw_lm_sensor_data = get_raw_lm_sensor_data()
  sensor_data = {'CPUTemps': {}, 'Others': {}}

  # Parse lm_sensor data
  for adapter, sources in raw_lm_sensor_data.items():
    section = 'Others'
    if LM_SENSORS_CPU_REGEX.search(adapter):
      section = 'CPUTemps'
    sensor_data[section][adapter] = {}
    sources.pop('Adapter', None)

    # Find current temp and add to dict
    ## current temp is labeled xxxx_input
    for source, labels in sources.items():
      for label, temp in labels.items():
        if label.startswith('fan') or label.startswith('in'):
          # Skip fan RPMs and voltages
          continue
        if 'input' in label:
          sensor_data[section][adapter][source] = {
            'Current': temp,
            'Label': label,
            'Max': temp,
            'Temps': [temp],
            }

    # Remove empty adapters
    if not sensor_data[section][adapter]:
      sensor_data[section].pop(adapter)

  # Remove empty sections
  for adapters in sensor_data.values():
    adapters = {source: source_data for source, source_data in adapters.items()
                if source_data}

  # Done
  return sensor_data


def get_raw_lm_sensor_data():
  """Get raw sensor data via lm_sensors, returns dict."""
  raw_lm_sensor_data = {}
  cmd = ['sensors', '-j']

  # Get raw data
  try:
    proc = run_program(cmd)
  except CalledProcessError:
    # Assuming no sensors available, return empty dict
    return {}

  # Workaround for bad sensors
  raw_data = []
  for line in proc.stdout.splitlines():
    if line.strip() == ',':
      # Assuming malformatted line caused by missing data
      continue
    raw_data.append(line)

  # Parse JSON data
  try:
    raw_lm_sensor_data = json.loads('\n'.join(raw_data))
  except json.JSONDecodeError:
    # Still broken, just return the empty dict
    pass

  # Done
  return raw_lm_sensor_data


def get_sensor_data():
  """Get sensor data via OS-specific means, returns dict."""
  sensor_data = {}
  if platform.system() == 'Darwin':
    sensor_data = get_smc_sensor_data()
  elif platform.system() == 'Linux':
    sensor_data = get_lm_sensor_data()

  return sensor_data


def get_smc_sensor_data():
  """Get sensor data via SMC, returns dict.

  NOTE: The data is structured like the lm_sensor data.
  """
  cmd = ['smc', '-l']
  sensor_data = {'CPUTemps': {'smc': {}}, 'Others': {'smc': {}}}

  # Parse SMC data
  proc = run_program(cmd)
  for line in proc.stdout.splitlines():
    tmp = SMC_REGEX.match(line.strip())
    if tmp:
      value = tmp.group('Value')
      try:
        LOG.debug('Invalid sensor: %s', tmp.group('ID'))
        value = float(value)
      except (TypeError, ValueError):
        # Skip this sensor
        continue

      # Only add known sensor IDs
      sensor_id = tmp.group('ID')
      if sensor_id not in SMC_IDS:
        continue

      # Add to dict
      section = 'Others'
      if SMC_IDS[sensor_id].get('CPUTemp', False):
        section = 'CPUTemps'
      source = SMC_IDS[sensor_id]['Source']
      sensor_data[section]['smc'][source] = {
        'Current': value,
        'Label': sensor_id,
        'Max': value,
        'Temps': [value],
        }

  # Done
  return sensor_data


def get_temp_str(temp, colored=True):
  """Get colored string based on temp, returns str."""
  temp_color = None

  # Safety check
  try:
    temp = float(temp)
  except (TypeError, ValueError):
    # Invalid temp?
    return color_string(temp, 'PURPLE')

  # Determine color
  if colored:
    for threshold, color in sorted(TEMP_COLORS.items(), reverse=True):
      if temp >= threshold:
        temp_color = color
        break

  # Done
  return color_string(f'{"-" if temp < 0 else ""}{temp:2.0f}°C', temp_color)



if __name__ == '__main__':
  print("This file is not meant to be called directly.")
