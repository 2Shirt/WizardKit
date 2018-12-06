# Wizard Kit: Functions - Sensors

import itertools
import json
import re
import shutil

from functions.tmux import *

# STATIC VARIABLES
TEMP_LIMITS = {
  'GREEN':  60,
  'YELLOW': 70,
  'ORANGE': 80,
  'RED':    90,
  }

# REGEX
REGEX_COLORS = re.compile(r'\033\[\d+;?1?m')

def clear_temps(sensor_data):
  """Clear saved temps but keep structure, returns dict."""
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        _data['Temps'] = []

def fix_sensor_str(s):
  """Cleanup string and return str."""
  s = re.sub(r'^(\w+)-(\w+)-(\w+)', r'\1 (\2 \3)', s, re.IGNORECASE)
  s = s.title()
  s = s.replace('Coretemp', 'CoreTemp')
  s = s.replace('Acpi', 'ACPI')
  s = s.replace('Isa ', 'ISA ')
  s = s.replace('Id ', 'ID ')
  s = re.sub(r'(\D+)(\d+)', r'\1 \2', s, re.IGNORECASE)
  s = s.replace('  ', ' ')
  return s

def generate_report(sensor_data, *temp_labels, colors=True):
  """Generate report based on temp_labels, returns list if str."""
  report = []
  for _section, _adapters in sorted(sensor_data.items()):
    # CoreTemps then Other temps
    for _adapter, _sources in sorted(_adapters.items()):
      # Adapter
      report.append(fix_sensor_str(_adapter))
      for _source, _data in sorted(_sources.items()):
        # Source
        _line = '{:18}  '.format(fix_sensor_str(_source))
        _temps = []
        # Temps (skip label for Current)
        for _label in temp_labels:
          _temps.append('{}{}{}'.format(
            _label.lower() if _label != 'Current' else '',
            ': ' if _label != 'Current' else '',
            get_temp_str(_data.get(_label, '???'), colors=colors)))
        _line += ', '.join(_temps)
        report.append(_line)
      report.append(' ')

  # Wrap lines if necessary
  screen_size = shutil.get_terminal_size()
  rows = screen_size.lines - 1
  if len(report) > rows and screen_size.columns > 55*2:
    report = list(itertools.zip_longest(
    report[:rows], report[rows:], fillvalue=''))
    report = [join_columns(a, b) for a, b in report]

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
    color = color,
    prefix = '-' if temp < 0 else '',
    temp = temp,
    **COLORS)

def get_raw_sensor_data():
  """Read sensor data and return dict."""
  cmd = ['sensors', '-j']
  result = run_program(cmd)
  return json.loads(result.stdout.decode())

def get_sensor_data():
  """Parse raw sensor data and return new dict."""
  json_data = get_raw_sensor_data()
  sensor_data = {'CoreTemps': {}, 'Other': {}}
  for _adapter, _sources in json_data.items():
    if 'coretemp' in _adapter:
      _section = 'CoreTemps'
    else:
      _section = 'Other'
    sensor_data[_section][_adapter] = {}
    _sources.pop('Adapter', None)

    # Find current temp and add to dict
    ## current temp is labeled xxxx_input
    for _source, _labels in _sources.items():
      for _label, _temp in _labels.items():
        if 'input' in _label:
          sensor_data[_section][_adapter][_source] = {
            'Current': _temp,
            'Label': _label,
            'Max': _temp,
            'Temps': [_temp],
            }

  # Remove empty sections
  for k, v in sensor_data.items():
    v = {k2: v2 for k2, v2 in v.items() if v2}

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

def monitor_sensors(monitor_pane, monitor_file):
  """Continually update sensor data and report to screen."""
  sensor_data = get_sensor_data()
  while True:
    update_sensor_data(sensor_data)
    with open(monitor_file, 'w') as f:
      report = generate_report(sensor_data, 'Current', 'Max')
      f.write('\n'.join(report))
    sleep(1)
    if not tmux_poll_pane(monitor_pane):
      break

def save_average_temp(sensor_data, temp_label, seconds=10):
  """Calculate average temps and record under temp_label, returns dict."""
  clear_temps(sensor_data)

  # Get temps
  for i in range(seconds):
    update_sensor_data(sensor_data)
    sleep(1)

  # Calculate averages
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        _data[temp_label] = sum(_data['Temps']) / len(_data['Temps'])

def update_sensor_data(sensor_data):
  """Read sensors and update existing sensor_data, returns dict."""
  json_data = get_raw_sensor_data()
  for _section, _adapters in sensor_data.items():
    for _adapter, _sources in _adapters.items():
      for _source, _data in _sources.items():
        _label = _data['Label']
        _temp = json_data[_adapter][_source][_label]
        _data['Current'] = _temp
        _data['Max'] = max(_temp, _data['Max'])
        _data['Temps'].append(_temp)

def join_columns(column1, column2, width=55):
  return '{:<{}}{}'.format(
    column1,
    55+len(column1)-len(REGEX_COLORS.sub('', column1)),
    column2)

if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
