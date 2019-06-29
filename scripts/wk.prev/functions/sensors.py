'''Wizard Kit: Functions - Sensors'''
# pylint: disable=no-name-in-module,wildcard-import
# vim: sts=2 sw=2 ts=2

import json
import re

from functions.tmux import *
from settings.sensors import *


# Error Classes
class ThermalLimitReachedError(Exception):
  '''Thermal limit reached error.'''


def clear_temps(sensor_data):
  """Clear saved temps but keep structure, returns dict."""
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        _data['Temps'] = []


def fix_sensor_str(_s):
  """Cleanup string and return str."""
  _s = re.sub(r'^(\w+)-(\w+)-(\w+)', r'\1 (\2 \3)', _s, re.IGNORECASE)
  _s = _s.title()
  _s = _s.replace('Coretemp', 'CPUTemp')
  _s = _s.replace('Acpi', 'ACPI')
  _s = _s.replace('ACPItz', 'ACPI TZ')
  _s = _s.replace('Isa ', 'ISA ')
  _s = _s.replace('Pci ', 'PCI ')
  _s = _s.replace('Id ', 'ID ')
  _s = re.sub(r'(\D+)(\d+)', r'\1 \2', _s, re.IGNORECASE)
  _s = re.sub(r'^K (\d+)Temp', r'AMD K\1 Temps', _s, re.IGNORECASE)
  _s = re.sub(r'T(ctl|die)', r'CPU (T\1)', _s, re.IGNORECASE)
  return _s


def generate_sensor_report(
    sensor_data, *temp_labels,
    colors=True, cpu_only=False):
  """Generate report based on temp_labels, returns list if str."""
  report = []
  for _section, _adapters in sorted(sensor_data.items()):
    # CPU temps then Other temps
    if cpu_only and 'CPU' not in _section:
      continue
    for _adapter, _sources in sorted(_adapters.items()):
      # Adapter
      report.append(fix_sensor_str(_adapter))
      for _source, _data in sorted(_sources.items()):
        # Source
        _line = '{:18}  '.format(fix_sensor_str(_source))
        # Temps (skip label for Current)
        for _label in temp_labels:
          _line += '{}{}{} '.format(
            _label.lower() if _label != 'Current' else '',
            ': ' if _label != 'Current' else '',
            get_temp_str(_data.get(_label, '???'), colors=colors))
        report.append(_line)
      if not cpu_only:
        report.append(' ')

  # Handle empty reports (i.e. no sensors detected)
  if not report:
    report = [
      '{}WARNING: No sensors found{}'.format(
        COLORS['YELLOW'] if colors else '',
        COLORS['CLEAR'] if colors else ''),
      ' ',
      'Please monitor temps manually']

  # Done
  return report


def get_colored_temp_str(temp):
  """Get colored string based on temp, returns str."""
  try:
    temp = float(temp)
  except ValueError:
    return '{YELLOW}{temp}{CLEAR}'.format(temp=temp, **COLORS)
  if temp > TEMP_LIMITS['RED']:
    color = COLORS['RED']
  elif temp > TEMP_LIMITS['ORANGE']:
    color = COLORS['ORANGE']
  elif temp > TEMP_LIMITS['YELLOW']:
    color = COLORS['YELLOW']
  elif temp > TEMP_LIMITS['GREEN']:
    color = COLORS['GREEN']
  elif temp > 0:
    color = COLORS['BLUE']
  else:
    color = COLORS['CLEAR']
  return '{color}{prefix}{temp:2.0f}°C{CLEAR}'.format(
    color=color,
    prefix='-' if temp < 0 else '',
    temp=temp,
    **COLORS)


def get_raw_sensor_data():
  """Read sensor data and return dict."""
  json_data = {}
  cmd = ['sensors', '-j']

  # Get raw data
  try:
    result = run_program(cmd)
    result = result.stdout.decode('utf-8', errors='ignore').splitlines()
  except subprocess.CalledProcessError:
    # Assuming no sensors available, set to empty list
    result = []

  # Workaround for bad sensors
  raw_data = []
  for line in result:
    if line.strip() == ',':
      # Assuming malformatted line caused by missing data
      continue
    raw_data.append(line)

  # Parse JSON data
  try:
    json_data = json.loads('\n'.join(raw_data))
  except json.JSONDecodeError:
    # Still broken, just return the empty dict
    pass

  # Done
  return json_data


def get_sensor_data():
  """Parse raw sensor data and return new dict."""
  json_data = get_raw_sensor_data()
  sensor_data = {'CPUTemps': {}, 'Other': {}}
  for _adapter, _sources in json_data.items():
    if is_cpu_adapter(_adapter):
      _section = 'CPUTemps'
    else:
      _section = 'Other'
    sensor_data[_section][_adapter] = {}
    _sources.pop('Adapter', None)

    # Find current temp and add to dict
    ## current temp is labeled xxxx_input
    for _source, _labels in _sources.items():
      for _label, _temp in _labels.items():
        if _label.startswith('fan'):
          # Skip fan RPMs
          continue
        if 'input' in _label:
          sensor_data[_section][_adapter][_source] = {
            'Current': _temp,
            'Label': _label,
            'Max': _temp,
            'Temps': [_temp],
            }

  # Remove empty sections
  for _k, _v in sensor_data.items():
    _v = {_k2: _v2 for _k2, _v2 in _v.items() if _v2}

  # Done
  return sensor_data


def get_temp_str(temp, colors=True):
  """Get temp string, returns str."""
  if colors:
    return get_colored_temp_str(temp)
  try:
    temp = float(temp)
  except ValueError:
    return '{}'.format(temp)
  else:
    return '{}{:2.0f}°C'.format(
      '-' if temp < 0 else '',
      temp)


def is_cpu_adapter(adapter):
  """Checks if adapter is a known CPU adapter, returns bool."""
  is_cpu = re.search(r'(core|k\d+)temp', adapter, re.IGNORECASE)
  return bool(is_cpu)


def monitor_sensors(monitor_pane, monitor_file):
  """Continually update sensor data and report to screen."""
  sensor_data = get_sensor_data()
  while True:
    update_sensor_data(sensor_data)
    with open(monitor_file, 'w') as _f:
      report = generate_sensor_report(sensor_data, 'Current', 'Max')
      _f.write('\n'.join(report))
    sleep(1)
    if monitor_pane and not tmux_poll_pane(monitor_pane):
      break


def save_average_temp(sensor_data, temp_label, seconds=10):
  """Save average temps under temp_label, returns dict."""
  clear_temps(sensor_data)

  # Get temps
  for _i in range(seconds): # pylint: disable=unused-variable
    update_sensor_data(sensor_data)
    sleep(1)

  # Calculate averages
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        _data[temp_label] = sum(_data['Temps']) / len(_data['Temps'])


def update_sensor_data(sensor_data, thermal_limit=None):
  """Read sensors and update existing sensor_data, returns dict."""
  json_data = get_raw_sensor_data()
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        try:
          _label = _data['Label']
          _temp = json_data[_adapter][_source][_label]
          _data['Current'] = _temp
          _data['Max'] = max(_temp, _data['Max'])
          _data['Temps'].append(_temp)
        except Exception: # pylint: disable=broad-except
          # Dumb workound for Dell sensors with changing source names
          pass

        # Check if thermal limit reached
        if thermal_limit and _section == 'CPUTemps':
          if max(_data['Current'], _data['Max']) >= thermal_limit:
            raise ThermalLimitReachedError('CPU temps reached limit')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
