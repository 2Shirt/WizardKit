"""WizardKit: Hardware sensors"""
# vim: sts=2 sw=2 ts=2

import json
import logging
import pathlib
import platform
import re

from subprocess import CalledProcessError

from wk.cfg.hw import CPU_CRITICAL_TEMP, SMC_IDS, TEMP_COLORS
from wk.exe import run_program, start_thread
from wk.std import color_string, sleep


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
LM_SENSORS_CPU_REGEX = re.compile(r'(core|k\d+)temp', re.IGNORECASE)
SMC_REGEX = re.compile(
  r'^\s*(?P<ID>\w{4})'
  r'\s+\[(?P<Type>.*)\]'
  r'\s+(?P<Value>.*?)'
  r'\s*\(bytes (?P<Bytes>.*)\)$'
  )
SENSOR_SOURCE_WIDTH = 25 if platform.system() == 'Darwin' else 20


# Error Classes
class ThermalLimitReachedError(RuntimeError):
  """Raised when the thermal threshold is reached."""


# Classes
class Sensors():
  """Class for holding sensor specific data."""
  def __init__(self):
    self.background_thread = None
    self.data = get_sensor_data()
    self.out_path = None

  def clear_temps(self):
    """Clear saved temps but keep structure"""
    for adapters in self.data.values():
      for sources in adapters.values():
        for source_data in sources.values():
          source_data['Temps'] = []

  def cpu_max_temp(self):
    """Get max temp from any CPU source, returns float.

    NOTE: If no temps are found this returns zero.
    """
    max_temp = 0.0

    # Check all CPU Temps
    for section, adapters in self.data.items():
      if not section.startswith('CPU'):
        continue
      for sources in adapters.values():
        for source_data in sources.values():
          max_temp = max(max_temp, source_data.get('Max', 0))

    # Done
    return max_temp

  def cpu_reached_critical_temp(self):
    """Check if CPU reached CPU_CRITICAL_TEMP, returns bool."""
    for section, adapters in self.data.items():
      if not section.startswith('CPU'):
        # Limit to CPU temps
        continue

      # Ugly section
      for sources in adapters.values():
        for source_data in sources.values():
          if source_data.get('Max', -1) >= CPU_CRITICAL_TEMP:
            return True

    # Didn't return above so temps are within the threshold
    return False

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
          line = f'{fix_sensor_name(source):{SENSOR_SOURCE_WIDTH}} '
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

  def monitor_to_file(self, out_path, temp_labels=None, thermal_action=None):
    """Write report to path every second until stopped.

    thermal_action is a cmd to run if ThermalLimitReachedError is caught.
    """
    stop_path = pathlib.Path(out_path).resolve().with_suffix('.stop')
    if not temp_labels:
      temp_labels = ('Current', 'Max')

    # Start loop
    while True:
      try:
        self.update_sensor_data()
      except ThermalLimitReachedError:
        if thermal_action:
          run_program(thermal_action, check=False)
      report = self.generate_report(*temp_labels)
      with open(out_path, 'w') as _f:
        _f.write('\n'.join(report))

      # Check if we should stop
      if stop_path.exists():
        break

      # Sleep before next loop
      sleep(0.5)

  def save_average_temps(self, temp_label, seconds=10):
    # pylint: disable=unused-variable
    """Save average temps under temp_label over provided seconds.."""
    self.clear_temps()

    # Get temps
    for i in range(seconds):
      self.update_sensor_data()
      sleep(1)

    # Calculate averages
    for adapters in self.data.values():
      for sources in adapters.values():
        for source_data in sources.values():
          temps = source_data['Temps']
          source_data[temp_label] = sum(temps) / len(temps)

  def start_background_monitor(
      self, out_path, temp_labels=None, thermal_action=None):
    """Start background thread to save report to file.

    thermal_action is a cmd to run if ThermalLimitReachedError is caught.
    """
    if self.background_thread:
      raise RuntimeError('Background thread already running')

    self.out_path = pathlib.Path(out_path)
    self.background_thread = start_thread(
      self.monitor_to_file,
      args=(out_path, temp_labels, thermal_action),
      )

  def stop_background_monitor(self):
    """Stop background thread."""
    self.out_path.with_suffix('.stop').touch()
    self.background_thread.join()

    # Reset vars to None
    self.background_thread = None
    self.out_path = None

  def update_sensor_data(self, exit_on_thermal_limit=True):
    """Update sensor data via OS-specific means."""
    if platform.system() == 'Darwin':
      self.update_sensor_data_macos(exit_on_thermal_limit)
    elif platform.system() == 'Linux':
      self.update_sensor_data_linux(exit_on_thermal_limit)

  def update_sensor_data_linux(self, exit_on_thermal_limit=True):
    """Update sensor data via lm_sensors."""
    lm_sensor_data = get_sensor_data_lm()
    for section, adapters in self.data.items():
      for adapter, sources in adapters.items():
        for source, source_data in sources.items():
          try:
            label = source_data['Label']
            temp = lm_sensor_data[adapter][source][label]
            source_data['Current'] = temp
            source_data['Max'] = max(temp, source_data['Max'])
            source_data['Temps'].append(temp)
          except KeyError:
            # Dumb workaround for Dell sensors with changing source names
            pass

          # Raise exception if thermal limit reached
          if exit_on_thermal_limit and section == 'CPUTemps':
            if source_data['Current'] >= CPU_CRITICAL_TEMP:
              raise ThermalLimitReachedError('CPU temps reached limit')

  def update_sensor_data_macos(self, exit_on_thermal_limit=True):
    """Update sensor data via SMC."""
    for section, adapters in self.data.items():
      for sources in adapters.values():
        for source_data in sources.values():
          cmd = ['smc', '-k', source_data['Label'], '-r']
          proc = run_program(cmd)
          match = SMC_REGEX.match(proc.stdout.strip())
          try:
            temp = float(match.group('Value'))
          except (TypeError, ValueError):
            LOG.error('Failed to update temp %s', source_data['Label'])
            continue

          # Update source
          source_data['Current'] = temp
          source_data['Max'] = max(temp, source_data['Max'])
          source_data['Temps'].append(temp)

          # Raise exception if thermal limit reached
          if exit_on_thermal_limit and section == 'CPUTemps':
            if source_data['Current'] >= CPU_CRITICAL_TEMP:
              raise ThermalLimitReachedError('CPU temps reached limit')


# Functions
def fix_sensor_name(name):
  """Cleanup sensor name, returns str."""
  name = re.sub(r'^(\w+)-(\w+)-(\w+)', r'\1 (\2 \3)', name, re.IGNORECASE)
  name = name.title()
  name = name.replace('ACPItz', 'ACPI TZ')
  name = name.replace('Acpi', 'ACPI')
  name = name.replace('Coretemp', 'CoreTemp')
  name = name.replace('Cpu', 'CPU')
  name = name.replace('Id ', 'ID ')
  name = name.replace('Isa ', 'ISA ')
  name = name.replace('Pci ', 'PCI ')
  name = name.replace('Smc', 'SMC')
  name = re.sub(r'(\D+)(\d+)', r'\1 \2', name, re.IGNORECASE)
  name = re.sub(r'^K (\d+)Temp', r'AMD K\1 Temps', name, re.IGNORECASE)
  name = re.sub(r'T(ctl|die)', r'CPU (T\1)', name, re.IGNORECASE)
  return name


def get_sensor_data():
  """Get sensor data via OS-specific means, returns dict."""
  sensor_data = {}
  if platform.system() == 'Darwin':
    sensor_data = get_sensor_data_macos()
  elif platform.system() == 'Linux':
    sensor_data = get_sensor_data_linux()

  return sensor_data


def get_sensor_data_linux():
  """Get sensor data via lm_sensors, returns dict."""
  raw_lm_sensor_data = get_sensor_data_lm()
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


def get_sensor_data_lm():
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


def get_sensor_data_macos():
  """Get sensor data via SMC, returns dict.

  NOTE: The data is structured like the lm_sensor data.
  """
  cmd = ['smc', '-l']
  sensor_data = {'CPUTemps': {'SMC (CPU)': {}}, 'Others': {'SMC (Other)': {}}}

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
      adapter = 'SMC (Other)'
      if SMC_IDS[sensor_id].get('CPU Temp', False):
        section = 'CPUTemps'
        adapter = 'SMC (CPU)'
      source = SMC_IDS[sensor_id]['Source']
      sensor_data[section][adapter][source] = {
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
