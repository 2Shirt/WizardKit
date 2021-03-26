"""WizardKit: Hardware diagnostics"""
# pylint: disable=too-many-lines
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
import re
import subprocess
import time

from collections import OrderedDict
from docopt import docopt

from wk import cfg, debug, exe, graph, log, net, std, tmux
from wk import os as wk_os
from wk.hw import obj as hw_obj
from wk.hw import sensors as hw_sensors


# STATIC VARIABLES
DOCSTRING = f'''{cfg.main.KIT_NAME_FULL}: Hardware Diagnostics

Usage:
  hw-diags [options]
  hw-diags (-h | --help)

Options:
  -c --cli            Force CLI mode
  -h --help           Show this page
  -q --quick          Skip menu and perform a quick check
'''
LOG = logging.getLogger(__name__)
BADBLOCKS_REGEX = re.compile(
  r'^Pass completed, (\d+) bad blocks found. .(\d+)/(\d+)/(\d+) errors',
  re.IGNORECASE,
  )
IO_GRAPH_WIDTH = 40
IO_ALT_TEST_SIZE_FACTOR = 0.01
IO_BLOCK_SIZE = 512 * 1024
IO_CHUNK_SIZE = 32 * 1024**2
IO_MINIMUM_TEST_SIZE = 10 * 1024**3
IO_RATE_REGEX = re.compile(
  r'(?P<bytes>\d+) bytes.* (?P<seconds>\S+) s(?:,|ecs )',
  )
MENU_ACTIONS = (
  'Audio Test',
  'Keyboard Test',
  'Network Test',
  'Start',
  'Quit')
MENU_ACTIONS_SECRET = (
  'Matrix',
  'Tubes',
  )
MENU_OPTIONS = (
  'CPU & Cooling',
  'Disk Attributes',
  'Disk Self-Test',
  'Disk Surface Scan',
  'Disk I/O Benchmark',
)
MENU_OPTIONS_QUICK = ('Disk Attributes',)
MENU_SETS = {
  'Full Diagnostic': (*MENU_OPTIONS,),
  'Disk Diagnostic': (
    'Disk Attributes',
    'Disk Self-Test',
    'Disk Surface Scan',
    'Disk I/O Benchmark',
    ),
  'Disk Diagnostic (Quick)': ('Disk Attributes',),
}
MENU_TOGGLES = (
  'Skip USB Benchmarks',
  )
PLATFORM = std.PLATFORM
STATUS_COLORS = {
  'Passed': 'GREEN',
  'Aborted': 'YELLOW',
  'N/A': 'YELLOW',
  'Skipped': 'YELLOW',
  'Unknown': 'YELLOW',
  'Working': 'YELLOW',
  'Denied': 'RED',
  'ERROR': 'RED',
  'Failed': 'RED',
  'TimedOut': 'RED',
  }


# Error Classes
class DeviceTooSmallError(RuntimeError):
  """Raised when a device is too small to test."""


# Classes
class State():
  """Object for tracking hardware diagnostic data."""
  def __init__(self):
    self.cpu = None
    self.disks = []
    self.layout = cfg.hw.TMUX_LAYOUT.copy()
    self.log_dir = None
    self.panes = {}
    self.tests = OrderedDict({
      'CPU & Cooling': {
        'Enabled': False,
        'Function': cpu_mprime_test,
        'Objects': [],
        },
      'Disk Attributes': {
        'Enabled': False,
        'Function': disk_attribute_check,
        'Objects': [],
        },
      'Disk Self-Test': {
        'Enabled': False,
        'Function': disk_self_test,
        'Objects': [],
        },
      'Disk Surface Scan': {
        'Enabled': False,
        'Function': disk_surface_scan,
        'Objects': [],
        },
      'Disk I/O Benchmark': {
        'Enabled': False,
        'Function': disk_io_benchmark,
        'Objects': [],
        },
      })
    self.top_text = std.color_string('Hardware Diagnostics', 'GREEN')

    # Init tmux and start a background process to maintain layout
    self.init_tmux()
    exe.start_thread(self.fix_tmux_layout_loop)

  def abort_testing(self):
    """Set unfinished tests as aborted and cleanup tmux panes."""
    for details in self.tests.values():
      for test in details['Objects']:
        if test.status in ('Pending', 'Working'):
          test.set_status('Aborted')

    # Cleanup tmux
    self.panes.pop('Current', None)
    for key, pane_ids in self.panes.copy().items():
      if key in ('Top', 'Started', 'Progress'):
        continue
      if isinstance(pane_ids, str):
        tmux.kill_pane(self.panes.pop(key))
      else:
        for _id in pane_ids:
          tmux.kill_pane(_id)
        self.panes.pop(key)

  def disk_safety_checks(self, prep=False, wait_for_self_tests=True):
    # pylint: disable=too-many-branches
    """Run disk safety checks."""
    self_tests_in_progress = False
    for disk in self.disks:
      disable_tests = False

      # Skip already disabled devices
      if all([test.disabled for test in disk.tests.values()]):
        continue

      try:
        disk.safety_checks()
      except hw_obj.CriticalHardwareError:
        disable_tests = True
        disk.add_note('Critical hardware error detected.', 'RED')
        if 'Disk Attributes' in disk.tests:
          disk.tests['Disk Attributes'].failed = True
          disk.tests['Disk Attributes'].set_status('Failed')
      except hw_obj.SMARTSelfTestInProgressError:
        if prep:
          std.print_warning(f'SMART self-test(s) in progress for {disk.path}')
          if std.ask('Continue with all tests disabled for this device?'):
            disable_tests = True
          else:
            std.print_standard('Diagnostics aborted.')
            std.print_standard(' ')
            std.pause('Press Enter to exit...')
            raise SystemExit(1)
        elif wait_for_self_tests:
          self_tests_in_progress = True
        else:
          # Other tests will NOT be disabled
          LOG.warning('SMART data may not be reliable for: %s', disk.path)
          # Add note to report
          if 'Disk Self-Test' in disk.tests:
            disk.tests['Disk Self-Test'].failed = True
            disk.tests['Disk Self-Test'].report.append(
              std.color_string('Please manually review SMART data', 'YELLOW'),
              )
      else:
        # No blocking errors encountered, check for minor attribute failures
        if ('Disk Attributes' in disk.tests
            and not disk.tests['Disk Attributes'].failed
            and not disk.check_attributes(only_blocking=False)):
          # Mid-diag failure detected
          LOG.warning('Disk attributes failure detected during diagnostics')
          disk.tests['Disk Attributes'].failed = True
          disk.tests['Disk Attributes'].set_status('Failed')

      # Disable tests if necessary
      if disable_tests:
        disk.disable_disk_tests()

    # Wait for self-test(s)
    if self_tests_in_progress:
      std.print_warning('SMART self-test(s) in progress')
      std.print_standard('Waiting 60 seconds before continuing...')
      std.sleep(60)
      self.disk_safety_checks(wait_for_self_tests=False)

  def fix_tmux_layout(self, forced=True):
    # pylint: disable=unused-argument
    """Fix tmux layout based on cfg.hw.TMUX_LAYOUT."""
    try:
      tmux.fix_layout(self.panes, self.layout, forced=forced)
    except RuntimeError:
      # Assuming self.panes changed while running
      pass

  def fix_tmux_layout_loop(self):
    """Fix tmux layout on a loop.

    NOTE: This should be called as a thread.
    """
    while True:
      self.fix_tmux_layout(forced=False)
      std.sleep(1)

  def init_diags(self, menu):
    """Initialize diagnostic pass."""

    # Reset objects
    self.disks.clear()
    self.layout.clear()
    self.layout.update(cfg.hw.TMUX_LAYOUT)
    for test_data in self.tests.values():
      test_data['Objects'].clear()

    # Set log
    self.log_dir = log.format_log_path()
    self.log_dir = pathlib.Path(
      f'{self.log_dir.parent}/'
      f'Hardware-Diagnostics_{time.strftime("%Y-%m-%d_%H%M%S%z")}/'
      )
    log.update_log_path(
      dest_dir=self.log_dir,
      dest_name='main',
      keep_history=False,
      timestamp=False,
      )
    std.clear_screen()
    std.print_info('Initializing...')

    # Progress Pane
    self.update_progress_pane()
    tmux.respawn_pane(
      pane_id=self.panes['Progress'],
      watch_file=f'{self.log_dir}/progress.out',
      )

    # Add HW Objects
    self.cpu = hw_obj.CpuRam()
    self.disks = hw_obj.get_disks(skip_kits=True)

    # Add test objects
    for name, details in menu.options.items():
      self.tests[name]['Enabled'] = details['Selected']
      if not details['Selected']:
        continue
      if 'CPU' in name:
        # Create two Test objects which will both be used by cpu_mprime_test
        # NOTE: Prime95 should be added first
        test_mprime_obj = hw_obj.Test(dev=self.cpu, label='Prime95')
        test_cooling_obj = hw_obj.Test(dev=self.cpu, label='Cooling')
        self.cpu.tests[test_mprime_obj.label] = test_mprime_obj
        self.cpu.tests[test_cooling_obj.label] = test_cooling_obj
        self.tests[name]['Objects'].append(test_mprime_obj)
        self.tests[name]['Objects'].append(test_cooling_obj)
      elif 'Disk' in name:
        for disk in self.disks:
          test_obj = hw_obj.Test(dev=disk, label=disk.path.name)
          disk.tests[name] = test_obj
          self.tests[name]['Objects'].append(test_obj)

    # Run safety checks
    self.disk_safety_checks(prep=True)

  def init_tmux(self):
    """Initialize tmux layout."""
    tmux.kill_all_panes()

    # Top
    self.panes['Top'] = tmux.split_window(
      behind=True,
      lines=2,
      vertical=True,
      text=f'{self.top_text}\nMain Menu',
      )

    # Started
    self.panes['Started'] = tmux.split_window(
      lines=cfg.hw.TMUX_SIDE_WIDTH,
      target_id=self.panes['Top'],
      text=std.color_string(
        ['Started', time.strftime("%Y-%m-%d %H:%M %Z")],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Progress
    self.panes['Progress'] = tmux.split_window(
      lines=cfg.hw.TMUX_SIDE_WIDTH,
      text=' ',
      )

  def save_debug_reports(self):
    """Save debug reports to disk."""
    LOG.info('Saving debug reports')
    debug_dir = pathlib.Path(f'{self.log_dir}/debug')
    if not debug_dir.exists():
      debug_dir.mkdir()

    # State (self)
    std.save_pickles({'state': self}, debug_dir)
    with open(f'{debug_dir}/state.report', 'a') as _f:
      _f.write('\n'.join(debug.generate_object_report(self)))

    # CPU/RAM
    with open(f'{debug_dir}/cpu.report', 'a') as _f:
      _f.write('\n'.join(debug.generate_object_report(self.cpu)))
      _f.write('\n\n[Tests]')
      for name, test in self.cpu.tests.items():
        _f.write(f'\n{name}:\n')
        _f.write('\n'.join(debug.generate_object_report(test, indent=1)))

    # Disks
    for disk in self.disks:
      with open(f'{debug_dir}/disk_{disk.path.name}.report', 'a') as _f:
        _f.write('\n'.join(debug.generate_object_report(disk)))
        _f.write('\n\n[Tests]')
        for name, test in disk.tests.items():
          _f.write(f'\n{name}:\n')
          _f.write('\n'.join(debug.generate_object_report(test, indent=1)))

  def update_progress_pane(self):
    """Update progress pane."""
    report = []
    width = cfg.hw.TMUX_SIDE_WIDTH

    for name, details in self.tests.items():
      if not details['Enabled']:
        continue

      # Add test details
      report.append(std.color_string(name, 'BLUE'))
      for test_obj in details['Objects']:
        report.append(std.color_string(
          [test_obj.label, f'{test_obj.status:>{width-len(test_obj.label)}}'],
          [None, STATUS_COLORS.get(test_obj.status, None)],
          sep='',
          ))

      # Add spacer
      report.append(' ')

    # Write to progress file
    out_path = pathlib.Path(f'{self.log_dir}/progress.out')
    with open(out_path, 'w') as _f:
      _f.write('\n'.join(report))

  def update_top_pane(self, text):
    """Update top pane with text."""
    tmux.respawn_pane(self.panes['Top'], text=f'{self.top_text}\n{text}')


# Functions
def audio_test():
  """Run an OS-specific audio test."""
  if PLATFORM == 'Linux':
    audio_test_linux()


def audio_test_linux():
  """Run an audio test using amixer and speaker-test."""
  LOG.info('Audio Test')

  # Set volume
  for source in ('Master', 'PCM'):
    cmd = f'amixer -q set "{source}" 80% unmute'.split()
    exe.run_program(cmd, check=False)

  # Run audio tests
  for mode in ('pink', 'wav'):
    cmd = f'speaker-test -c 2 -l 1 -t {mode}'.split()
    exe.run_program(cmd, check=False, pipe=False)


def build_menu(cli_mode=False, quick_mode=False):
  """Build main menu, returns wk.std.Menu."""
  menu = std.Menu(title=None)

  # Add actions, options, etc
  for action in MENU_ACTIONS:
    menu.add_action(action)
  for action in MENU_ACTIONS_SECRET:
    menu.add_action(action, {'Hidden': True})
  for option in MENU_OPTIONS:
    menu.add_option(option, {'Selected': True})
  for toggle in MENU_TOGGLES:
    menu.add_toggle(toggle, {'Selected': True})
  for name, targets in MENU_SETS.items():
    menu.add_set(name, {'Targets': targets})
  menu.actions['Start']['Separator'] = True

  # Update default selections for quick mode if necessary
  if quick_mode:
    for name in menu.options:
      # Only select quick option(s)
      menu.options[name]['Selected'] = name in MENU_OPTIONS_QUICK

  # Add CLI actions if necessary
  if cli_mode or 'DISPLAY' not in os.environ:
    menu.add_action('Reboot')
    menu.add_action('Power Off')

  # Compatibility checks
  if PLATFORM != 'Linux':
    for name in ('Audio Test', 'Keyboard Test'):
      menu.actions[name]['Disabled'] = True
  if PLATFORM not in ('Darwin', 'Linux'):
    for name in ('Matrix', 'Network Test', 'Tubes'):
      menu.actions[name]['Disabled'] = True

  # Done
  return menu


def calc_io_dd_values(dev_size):
  """Calculate I/O benchmark dd values, returns dict.

  Calculations:
  The minimum dev size is IO_GRAPH_WIDTH * IO_CHUNK_SIZE
    (e.g. 1.25 GB for a width of 40 and a chunk size of 32MB)

  read_total is the area to be read in bytes
    If the dev is < IO_MINIMUM_TEST_SIZE then it's the whole dev
    Else it's the larger of IO_MINIMUM_TEST_SIZE or the alt test size
    (determined by dev * IO_ALT_TEST_SIZE_FACTOR)

  read_chunks is the number of groups of IO_CHUNK_SIZE in test_obj.dev
    This number is reduced to a multiple of IO_GRAPH_WIDTH in order
    to allow for the data to be condensed cleanly

  read_blocks is the chunk size in number of blocks
    (e.g. 64 if block size is 512KB and chunk size is 32MB

  skip_total is the number of IO_BLOCK_SIZE groups not tested
  skip_blocks is the number of blocks to skip per IO_CHUNK_SIZE
  skip_extra_rate is how often to add an additional skip block
    This is needed to ensure an even testing across the dev
    This is calculated by using the fractional amount left off
    of the skip_blocks variable
  """
  read_total = min(IO_MINIMUM_TEST_SIZE, dev_size)
  read_total = max(read_total, dev_size*IO_ALT_TEST_SIZE_FACTOR)
  read_chunks = int(read_total // IO_CHUNK_SIZE)
  read_chunks -= read_chunks % IO_GRAPH_WIDTH
  if read_chunks < IO_GRAPH_WIDTH:
    raise DeviceTooSmallError
  read_blocks = int(IO_CHUNK_SIZE / IO_BLOCK_SIZE)
  read_total = read_chunks * IO_CHUNK_SIZE
  skip_total = int((dev_size - read_total) // IO_BLOCK_SIZE)
  skip_blocks = int((skip_total / read_chunks) // 1)
  skip_extra_rate = 0
  try:
    skip_extra_rate = 1 + int(1 / ((skip_total / read_chunks) % 1))
  except ZeroDivisionError:
    # skip_extra_rate == 0 is fine
    pass

  # Done
  return {
    'Read Chunks': read_chunks,
    'Read Blocks': read_blocks,
    'Skip Blocks': skip_blocks,
    'Skip Extra': skip_extra_rate,
    }


def check_cooling_results(test_obj, sensors):
  """Check cooling results and update test_obj."""
  max_temp = sensors.cpu_max_temp()

  # Check temps
  if not max_temp:
    test_obj.set_status('Unknown')
  elif max_temp >= cfg.hw.CPU_FAILURE_TEMP:
    test_obj.failed = True
    test_obj.set_status('Failed')
  elif 'Aborted' not in test_obj.status:
    test_obj.passed = True
    test_obj.set_status('Passed')

  # Add temps to report
  for line in sensors.generate_report(
      'Idle', 'Max', 'Cooldown', only_cpu=True):
    test_obj.report.append(f'  {line}')


def check_io_benchmark_results(test_obj, rate_list, graph_width):
  """Generate colored report using rate_list, returns list of str."""
  avg_read = sum(rate_list) / len(rate_list)
  min_read = min(rate_list)
  max_read = max(rate_list)
  if test_obj.dev.details['ssd']:
    thresh_min = cfg.hw.THRESH_SSD_MIN
    thresh_avg_high = cfg.hw.THRESH_SSD_AVG_HIGH
    thresh_avg_low = cfg.hw.THRESH_SSD_AVG_LOW
  else:
    thresh_min = cfg.hw.THRESH_HDD_MIN
    thresh_avg_high = cfg.hw.THRESH_HDD_AVG_HIGH
    thresh_avg_low = cfg.hw.THRESH_HDD_AVG_LOW

  # Add horizontal graph to report
  for line in graph.generate_horizontal_graph(rate_list, graph_width):
    if not std.strip_colors(line).strip():
      # Skip empty lines
      continue
    test_obj.report.append(line)

  # Add read rates to report
  test_obj.report.append(
    f'Read speeds    avg: {avg_read/(1000**2):3.1f}'
    f' min: {min_read/(1000**2):3.1f}'
    f' max: {max_read/(1000**2):3.1f}'
    )

  # Compare against thresholds
  if min_read <= thresh_min and avg_read <= thresh_avg_high:
    test_obj.failed = True
  elif avg_read <= thresh_avg_low:
    test_obj.failed = True
  else:
    test_obj.passed = True

  # Set status
  if test_obj.failed:
    test_obj.set_status('Failed')
  elif test_obj.passed:
    test_obj.set_status('Passed')
  else:
    test_obj.set_status('Unknown')


def check_mprime_results(test_obj, working_dir):
  """Check mprime log files and update test_obj."""
  passing_lines = {}
  warning_lines = {}

  def _read_file(log_name):
    """Read file and split into lines, returns list."""
    lines = []
    try:
      with open(f'{working_dir}/{log_name}', 'r') as _f:
        lines = _f.readlines()
    except FileNotFoundError:
      # File may be missing on older systems
      lines = []

    return lines

  # results.txt (check if failed)
  for line in _read_file('results.txt'):
    line = line.strip()
    if re.search(r'(error|fail)', line, re.IGNORECASE):
      warning_lines[line] = None

  # print.log (check if passed)
  for line in _read_file('prime.log'):
    line = line.strip()
    match = re.search(
      r'(completed.*(\d+) errors, (\d+) warnings)', line, re.IGNORECASE)
    if match:
      if int(match.group(2)) + int(match.group(3)) > 0:
        # Errors and/or warnings encountered
        warning_lines[match.group(1).capitalize()] = None
      else:
        # No errors/warnings
        passing_lines[match.group(1).capitalize()] = None

  # Update status
  if warning_lines:
    test_obj.failed = True
    test_obj.set_status('Failed')
  elif passing_lines and 'Aborted' not in test_obj.status:
    test_obj.passed = True
    test_obj.set_status('Passed')
  else:
    test_obj.set_status('Unknown')

  # Update report
  for line in passing_lines:
    test_obj.report.append(f'  {line}')
  for line in warning_lines:
    test_obj.report.append(std.color_string(f'  {line}', 'YELLOW'))
  if not (passing_lines or warning_lines):
    test_obj.report.append(std.color_string('  Unknown result', 'YELLOW'))


def check_self_test_results(test_obj, aborted=False):
  """Check SMART self-test results."""
  test_obj.report.append(std.color_string('Self-Test', 'BLUE'))
  if test_obj.disabled or test_obj.status == 'Denied':
    test_obj.report.append(std.color_string(f'  {test_obj.status}', 'RED'))
  elif test_obj.status == 'N/A' or not test_obj.dev.attributes:
    test_obj.report.append(std.color_string(f'  {test_obj.status}', 'YELLOW'))
  else:
    # Not updating SMART data here to preserve the test status for the report
    # For instance if the test was aborted the report should inlcude the last
    # known progress instead of just "was aborted buy host"
    test_details = test_obj.dev.get_smart_self_test_details()
    test_result = test_details.get('status', {}).get('string', 'Unknown')
    test_obj.report.append(f'  {test_result.capitalize()}')
    if aborted and not (test_obj.passed or test_obj.failed):
      test_obj.report.append(std.color_string('  Aborted', 'YELLOW'))
      test_obj.set_status('Aborted')
    elif test_obj.status == 'TimedOut':
      test_obj.report.append(std.color_string('  TimedOut', 'YELLOW'))
      test_obj.set_status('TimedOut')
    else:
      test_obj.failed = not test_obj.passed
      if test_obj.failed:
        test_obj.set_status('Failed')


def cpu_mprime_test(state, test_objects):
  # pylint: disable=too-many-statements
  """CPU & cooling check using Prime95."""
  LOG.info('CPU Test (Prime95)')
  aborted = False
  prime_log = pathlib.Path(f'{state.log_dir}/prime.log')
  sensors_out = pathlib.Path(f'{state.log_dir}/sensors.out')
  test_mprime_obj, test_cooling_obj = test_objects

  # Bail early
  if test_cooling_obj.disabled or test_mprime_obj.disabled:
    return

  # Prep
  state.update_top_pane(test_mprime_obj.dev.description)
  test_cooling_obj.set_status('Working')
  test_mprime_obj.set_status('Working')

  # Start sensors monitor
  sensors = hw_sensors.Sensors()
  sensors.start_background_monitor(
    sensors_out,
    thermal_action=('killall', 'mprime', '-INT'),
    )

  # Create monitor and worker panes
  state.update_progress_pane()
  state.panes['Prime95'] = tmux.split_window(
    lines=10, vertical=True, watch_file=prime_log)
  if PLATFORM == 'Darwin':
    state.panes['Temps'] = tmux.split_window(
      behind=True, percent=80, vertical=True, cmd='./hw-sensors')
  elif PLATFORM == 'Linux':
    state.panes['Temps'] = tmux.split_window(
      behind=True, percent=80, vertical=True, watch_file=sensors_out)
  tmux.resize_pane(height=3)
  state.panes['Current'] = ''
  state.layout['Current'] = {'height': 3, 'Check': True}

  # Get idle temps
  std.print_standard('Saving idle temps...')
  sensors.save_average_temps(temp_label='Idle', seconds=5)

  # Stress CPU
  std.print_info('Starting stress test')
  set_apple_fan_speed('max')
  proc_mprime = start_mprime(state.log_dir, prime_log)

  # Show countdown
  print('')
  try:
    print_countdown(proc=proc_mprime, seconds=cfg.hw.CPU_TEST_MINUTES*60)
  except KeyboardInterrupt:
    aborted = True

  # Stop Prime95
  stop_mprime(proc_mprime)

  # Update progress if necessary
  if sensors.cpu_reached_critical_temp() or aborted:
    test_cooling_obj.set_status('Aborted')
    test_mprime_obj.set_status('Aborted')
    state.update_progress_pane()

  # Get cooldown temp
  std.clear_screen()
  std.print_standard('Letting CPU cooldown...')
  std.sleep(5)
  std.print_standard('Saving cooldown temps...')
  sensors.save_average_temps(temp_label='Cooldown', seconds=5)

  # Check Prime95 results
  test_mprime_obj.report.append(std.color_string('Prime95', 'BLUE'))
  check_mprime_results(test_obj=test_mprime_obj, working_dir=state.log_dir)

  # Check Cooling results
  test_cooling_obj.report.append(std.color_string('Temps', 'BLUE'))
  check_cooling_results(test_obj=test_cooling_obj, sensors=sensors)

  # Cleanup
  state.update_progress_pane()
  sensors.stop_background_monitor()
  state.panes.pop('Current', None)
  tmux.kill_pane(state.panes.pop('Prime95', None))
  tmux.kill_pane(state.panes.pop('Temps', None))

  # Done
  if aborted:
    raise std.GenericAbort('Aborted')


def disk_attribute_check(state, test_objects):
  """Disk attribute check."""
  LOG.info('Disk Attribute Check')
  for test in test_objects:
    if not test.dev.attributes:
      # No NVMe/SMART data
      test.set_status('N/A')
      continue

    if test.dev.check_attributes():
      test.passed = True
      test.set_status('Passed')
    else:
      test.failed = True
      test.set_status('Failed')

  # Done
  state.update_progress_pane()


def disk_io_benchmark(state, test_objects, skip_usb=True):
  # pylint: disable=too-many-statements
  """Disk I/O benchmark using dd."""
  LOG.info('Disk I/O Benchmark (dd)')
  aborted = False

  def _run_io_benchmark(test_obj, log_path):
    """Run I/O benchmark and handle exceptions."""
    dev_path = test_obj.dev.path
    if PLATFORM == 'Darwin':
      # Use "RAW" disks under macOS
      dev_path = dev_path.with_name(f'r{dev_path.name}')
      LOG.info('Using %s for better performance', dev_path)
    offset = 0
    read_rates = []
    test_obj.report.append(std.color_string('I/O Benchmark', 'BLUE'))

    # Get dd values or bail
    try:
      dd_values = calc_io_dd_values(test_obj.dev.details['size'])
    except DeviceTooSmallError:
      test_obj.set_status('N/A')
      test_obj.report.append(
        std.color_string('Disk too small to test', 'YELLOW'),
        )
      return

    # Run dd read tests
    for _i in range(dd_values['Read Chunks']):
      _i += 1

      # Build cmd
      skip = dd_values['Skip Blocks']
      if dd_values['Skip Extra'] and _i % dd_values['Skip Extra'] == 0:
        skip += 1
      cmd = [
        'sudo', 'dd',
        f'bs={IO_BLOCK_SIZE}',
        f'skip={offset+skip}',
        f'count={dd_values["Read Blocks"]}',
        f'if={dev_path}',
        'of=/dev/null',
        ]
      if PLATFORM == 'Linux':
        cmd.append('iflag=direct')

      # Run and get read rate
      try:
        proc = exe.run_program(
          cmd,
          pipe=False,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          )
      except PermissionError:
        # Since we're using sudo we can't kill dd
        # Assuming this happened during a CTRL+c
        raise KeyboardInterrupt
      match = IO_RATE_REGEX.search(proc.stdout)
      if match:
        read_rates.append(
          int(match.group('bytes')) / float(match.group('seconds')),
          )
        match.group(1)

      # Show progress
      with open(log_path, 'a') as _f:
        if _i % 5 == 0:
          percent = (_i / dd_values['Read Chunks']) * 100
          _f.write(f'  {graph.vertical_graph_line(percent, read_rates[-1])}\n')

      # Update offset
      offset += dd_values['Read Blocks'] + skip

    # Check results
    check_io_benchmark_results(test_obj, read_rates, IO_GRAPH_WIDTH)

  # Run benchmarks
  state.update_top_pane(
    f'Disk I/O Benchmark{"s" if len(test_objects) > 1 else ""}',
    )
  state.panes['I/O Benchmark'] = tmux.split_window(
    percent=50,
    vertical=True,
    text=' ',
    )
  for test in test_objects:
    if test.disabled:
      # Skip
      continue

    # Skip USB devices if requested
    if skip_usb and test.dev.details['bus'] == 'USB':
      test.set_status('Skipped')
      continue

    # Start benchmark
    if not aborted:
      std.clear_screen()
      std.print_report(test.dev.generate_report())
      test.set_status('Working')
      test_log = f'{state.log_dir}/{test.dev.path.name}_benchmark.out'
      tmux.respawn_pane(
        state.panes['I/O Benchmark'],
        watch_cmd='tail',
        watch_file=test_log,
        )
      state.update_progress_pane()
      try:
        _run_io_benchmark(test, test_log)
      except KeyboardInterrupt:
        aborted = True
      except (subprocess.CalledProcessError, TypeError, ValueError) as err:
        # Something went wrong
        LOG.error('%s', err)
        test.set_status('ERROR')
        test.report.append(std.color_string('  Unknown Error', 'RED'))

    # Mark test(s) aborted if necessary
    if aborted:
      test.set_status('Aborted')
      test.report.append(std.color_string('  Aborted', 'YELLOW'))

    # Update progress after each test
    state.update_progress_pane()

  # Cleanup
  state.update_progress_pane()
  tmux.kill_pane(state.panes.pop('I/O Benchmark', None))

  # Done
  if aborted:
    raise std.GenericAbort('Aborted')


def disk_self_test(state, test_objects):
  # pylint: disable=too-many-statements
  """Disk self-test if available."""
  LOG.info('Disk Self-Test(s)')
  aborted = False
  threads = []
  state.panes['SMART'] = []

  def _run_self_test(test_obj, log_path):
    """Run self-test and handle exceptions."""
    result = None

    try:
      test_obj.passed = test_obj.dev.run_self_test(log_path)
    except TimeoutError:
      test_obj.failed = True
      result = 'TimedOut'
    except hw_obj.SMARTNotSupportedError:
      # Pass test since it doesn't apply
      test_obj.passed = True
      result = 'N/A'

    # Set status
    if result:
      test_obj.set_status(result)
    else:
      if test_obj.failed:
        test_obj.set_status('Failed')
      elif test_obj.passed:
        test_obj.set_status('Passed')
      else:
        test_obj.set_status('Unknown')

  # Run self-tests
  state.update_top_pane(
    f'Disk self-test{"s" if len(test_objects) > 1 else ""}',
    )
  std.print_info(f'Starting self-test{"s" if len(test_objects) > 1 else ""}')
  for test in reversed(test_objects):
    if test.disabled:
      # Skip
      continue

    # Start thread
    test.set_status('Working')
    test_log = f'{state.log_dir}/{test.dev.path.name}_selftest.log'
    threads.append(exe.start_thread(_run_self_test, args=(test, test_log)))

    # Show progress
    if threads[-1].is_alive():
      state.panes['SMART'].append(
        tmux.split_window(lines=4, vertical=True, watch_file=test_log),
        )

  # Wait for all tests to complete
  state.update_progress_pane()
  try:
    while True:
      if any([t.is_alive() for t in threads]):
        std.sleep(1)
      else:
        break
  except KeyboardInterrupt:
    aborted = True
    for test in test_objects:
      test.dev.abort_self_test()
    std.sleep(0.5)

  # Save report(s)
  for test in test_objects:
    check_self_test_results(test, aborted=aborted)

  # Cleanup
  state.update_progress_pane()
  for pane in state.panes['SMART']:
    tmux.kill_pane(pane)
  state.panes.pop('SMART', None)

  # Done
  if aborted:
    raise std.GenericAbort('Aborted')


def disk_surface_scan(state, test_objects):
  # pylint: disable=too-many-statements
  """Read-only disk surface scan using badblocks."""
  LOG.info('Disk Surface Scan (badblocks)')
  aborted = False
  threads = []
  state.panes['badblocks'] = []

  def _run_surface_scan(test_obj, log_path):
    """Run surface scan and handle exceptions."""
    block_size = '1024'
    dev = test_obj.dev
    dev_path = test_obj.dev.path
    if PLATFORM == 'Darwin':
      # Use "RAW" disks under macOS
      dev_path = dev_path.with_name(f'r{dev_path.name}')
      LOG.info('Using %s for better performance', dev_path)
    test_obj.report.append(std.color_string('badblocks', 'BLUE'))
    test_obj.set_status('Working')

    # Increase block size if necessary
    if (dev.details['phy-sec'] == 4096
        or dev.details['size'] >= cfg.hw.BADBLOCKS_LARGE_DISK):
      block_size = '4096'

    # Start scan
    cmd = ['sudo', 'badblocks', '-sv', '-b', block_size, '-e', '1', dev_path]
    with open(log_path, 'a') as _f:
      size_str = std.bytes_to_string(dev.details["size"], use_binary=False)
      _f.write(
        std.color_string(
          ['[', dev.path.name, ' ', size_str, ']\n'],
          [None, 'BLUE', None, 'CYAN', None],
          sep='',
          ),
        )
      _f.flush()
      exe.run_program(
        cmd,
        check=False,
        pipe=False,
        stderr=subprocess.STDOUT,
        stdout=_f,
        )

    # Check results
    with open(log_path, 'r') as _f:
      for line in _f.readlines():
        line = std.strip_colors(line.strip())
        if not line or line.startswith('Checking') or line.startswith('['):
          # Skip
          continue
        match = BADBLOCKS_REGEX.search(line)
        if match:
          if all([s == '0' for s in match.groups()]):
            test_obj.passed = True
            test_obj.report.append(f'  {line}')
            test_obj.set_status('Passed')
          else:
            test_obj.failed = True
            test_obj.report.append(f'  {std.color_string(line, "YELLOW")}')
            test_obj.set_status('Failed')
        else:
          test_obj.report.append(f'  {std.color_string(line, "YELLOW")}')
    if not (test_obj.passed or test_obj.failed):
      test_obj.set_status('Unknown')

  # Run surface scans
  state.update_top_pane(
    f'Disk Surface Scan{"s" if len(test_objects) > 1 else ""}',
    )
  std.print_info(
    f'Starting disk surface scan{"s" if len(test_objects) > 1 else ""}',
    )
  for test in reversed(test_objects):
    if test.disabled:
      # Skip
      continue

    # Start thread
    test_log = f'{state.log_dir}/{test.dev.path.name}_badblocks.log'
    threads.append(exe.start_thread(_run_surface_scan, args=(test, test_log)))

    # Show progress
    if threads[-1].is_alive():
      state.panes['badblocks'].append(
        tmux.split_window(
          lines=5,
          vertical=True,
          watch_cmd='tail',
          watch_file=test_log,
          ),
        )

  # Wait for all tests to complete
  try:
    while True:
      if any([t.is_alive() for t in threads]):
        state.update_progress_pane()
        std.sleep(5)
      else:
        break
  except KeyboardInterrupt:
    aborted = True
    std.sleep(0.5)
    # Handle aborts
    for test in test_objects:
      if not (test.disabled or test.passed or test.failed):
        test.set_status('Aborted')
        test.report.append(std.color_string('  Aborted', 'YELLOW'))

  # Cleanup
  state.update_progress_pane()
  for pane in state.panes['badblocks']:
    tmux.kill_pane(pane)
  state.panes.pop('badblocks', None)

  # Done
  if aborted:
    raise std.GenericAbort('Aborted')


def keyboard_test():
  """Test keyboard using xev."""
  LOG.info('Keyboard Test (xev)')
  cmd = ['xev', '-event', 'keyboard']
  exe.run_program(cmd, check=False, pipe=False)


def main():
  # pylint: disable=too-many-branches
  """Main function for hardware diagnostics."""
  args = docopt(DOCSTRING)
  log.update_log_path(dest_name='Hardware-Diagnostics', timestamp=True)

  # Safety check
  if 'TMUX' not in os.environ:
    LOG.error('tmux session not found')
    raise RuntimeError('tmux session not found')

  # Init
  atexit.register(tmux.kill_all_panes)
  menu = build_menu(cli_mode=args['--cli'], quick_mode=args['--quick'])
  state = State()

  # Quick Mode
  if args['--quick']:
    run_diags(state, menu, quick_mode=True)
    return

  # Show menu
  while True:
    action = None
    selection = menu.advanced_select()

    # Set action
    if 'Audio Test' in selection:
      action = audio_test
    elif 'Keyboard Test' in selection:
      action = keyboard_test
    elif 'Network Test' in selection:
      action = network_test

    # Run simple test
    if action:
      state.update_top_pane(selection[0])
      try:
        action()
      except KeyboardInterrupt:
        std.print_warning('Aborted.')
        std.print_standard('')
        std.pause('Press Enter to return to main menu...')

    # Secrets
    if 'Matrix' in selection:
      screensaver('matrix')
    elif 'Tubes' in selection:
      # Tubes ≈≈ Pipes?
      screensaver('pipes')

    # Quit
    if 'Reboot' in selection:
      cmd = ['/usr/local/bin/wk-power-command', 'reboot']
      exe.run_program(cmd, check=False)
    elif 'Power Off' in selection:
      cmd = ['/usr/local/bin/wk-power-command', 'poweroff']
      exe.run_program(cmd, check=False)
    elif 'Quit' in selection:
      break

    # Start diagnostics
    if 'Start' in selection:
      run_diags(state, menu, quick_mode=False)

    # Reset top pane
    state.update_top_pane('Main Menu')


def network_test():
  """Run network tests."""
  LOG.info('Network Test')
  try_and_print = std.TryAndPrint()
  result = try_and_print.run(
    message='Network connection...',
    function=net.connected_to_private_network,
    msg_good='OK',
    raise_on_error=True,
    )

  # Bail if not connected
  if result['Failed']:
    std.print_warning('Please connect to a network and try again')
    std.pause('Press Enter to return to main menu...')
    return

  # Show IP address(es)
  net.show_valid_addresses()

  # Ping tests
  try_and_print.run(
    'Internet connection...', net.ping, msg_good='OK', addr='8.8.8.8')
  try_and_print.run(
    'DNS resolution...', net.ping, msg_good='OK', addr='google.com')

  # Speedtest
  try_and_print.run('Speedtest...', net.speedtest)

  # Done
  std.pause('Press Enter to return to main menu...')


def print_countdown(proc, seconds):
  """Print countdown to screen while proc is alive."""
  for i in range(seconds):
    sec_left = (seconds - i) % 60
    min_left = int((seconds - i) / 60)

    out_str = '\r  '
    if min_left:
      out_str += f'{min_left} minute{"s" if min_left != 1 else ""}, '
    out_str += f'{sec_left} second{"s" if sec_left != 1 else ""}'
    out_str += ' remaining'

    print(f'{out_str:<42}', end='', flush=True)
    try:
      proc.wait(1)
    except subprocess.TimeoutExpired:
      # proc still going, continue
      pass
    if proc.poll() is not None:
      # proc exited, stop countdown
      break

  # Done
  print('')


def run_diags(state, menu, quick_mode=False):
  """Run selected diagnostics."""
  aborted = False
  atexit.register(state.save_debug_reports)
  state.init_diags(menu)

  # Just return if no tests were selected
  if not any([details['Enabled'] for details in state.tests.values()]):
    std.print_warning('No tests selected?')
    std.pause()
    return

  # Run tests
  for name, details in state.tests.items():
    if not details['Enabled']:
      # Skip disabled tests
      continue

    # Run test(s)
    function = details['Function']
    args = [details['Objects']]
    if name == 'Disk I/O Benchmark':
      args.append(menu.toggles['Skip USB Benchmarks']['Selected'])
    std.clear_screen()
    try:
      function(state, *args)
    except (KeyboardInterrupt, std.GenericAbort):
      aborted = True
      state.abort_testing()
      state.update_progress_pane()
      break

    # Run safety checks
    if name.startswith('Disk'):
      state.disk_safety_checks(wait_for_self_tests=name != 'Disk Attributes')

  # Handle aborts
  if aborted:
    for details in state.tests.values():
      for test_obj in details['Objects']:
        if test_obj.status == 'Pending':
          test_obj.set_status('Aborted')

  # Show results
  show_results(state)

  # Done
  state.save_debug_reports()
  atexit.unregister(state.save_debug_reports)
  if quick_mode:
    std.pause('Press Enter to exit...')
  else:
    std.pause('Press Enter to return to main menu...')


def screensaver(name):
  """Show screensaver"""
  LOG.info('Screensaver (%s)', name)
  if name == 'matrix':
    cmd = ['cmatrix', '-abs']
  elif name == 'pipes':
    cmd = [
      'pipes' if PLATFORM == 'Linux' else 'pipes.sh',
      '-t', '0',
      '-t', '1',
      '-t', '2',
      '-t', '3',
      '-t', '5',
      '-R', '-r', '4000',
      ]

  # Switch pane to fullscreen and start screensaver
  tmux.zoom_pane()
  exe.run_program(cmd, check=False, pipe=False, stderr=subprocess.PIPE)
  tmux.zoom_pane()


def set_apple_fan_speed(speed):
  """Set Apple fan speed."""
  cmd = None

  # Check
  if speed not in ('auto', 'max'):
    raise RuntimeError(f'Invalid speed {speed}')

  # Set cmd
  if PLATFORM == 'Darwin':
    try:
      wk_os.mac.set_fans(speed)
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as err:
      LOG.error('Failed to set fans to %s', speed)
      LOG.error('Error: %s', err)
      std.print_error(f'Failed to set fans to {speed}')
      for line in str(err).splitlines():
        std.print_warning(f'  {line.strip()}')
  elif PLATFORM == 'Linux':
    cmd = ['apple-fans', speed]
    exe.run_program(cmd, check=False)


def show_results(state):
  """Show test results by device."""
  std.sleep(0.5)
  std.clear_screen()
  state.update_top_pane('Results')

  # CPU Tests
  cpu_tests_enabled = [data['Enabled'] for name, data in state.tests.items()
                       if name.startswith('CPU')]
  if any(cpu_tests_enabled):
    std.print_success('CPU:')
    std.print_report(state.cpu.generate_report())
    std.print_standard(' ')

  # Disk Tests
  disk_tests_enabled = [data['Enabled'] for name, data in state.tests.items()
                        if name.startswith('Disk')]
  if any(disk_tests_enabled):
    std.print_success(f'Disk{"s" if len(state.disks) > 1 else ""}:')
    for disk in state.disks:
      std.print_report(disk.generate_report())
      std.print_standard(' ')
    if not state.disks:
      std.print_warning('No devices')
      std.print_standard(' ')


def start_mprime(working_dir, log_path):
  """Start mprime and save filtered output to log, returns Popen object."""
  set_apple_fan_speed('max')
  proc_mprime = subprocess.Popen(
    ['mprime', '-t'],
    cwd=working_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    )
  proc_grep = subprocess.Popen(
    'grep --ignore-case --invert-match --line-buffered stress.txt'.split(),
    stdin=proc_mprime.stdout,
    stdout=subprocess.PIPE,
    )
  proc_mprime.stdout.close()
  save_nsbr = exe.NonBlockingStreamReader(proc_grep.stdout)
  exe.start_thread(
    save_nsbr.save_to_file,
    args=(proc_grep, log_path),
    )

  # Return objects
  return proc_mprime


def stop_mprime(proc_mprime):
  """Stop mprime gracefully, then forcefully as needed."""
  proc_mprime.terminate()
  try:
    proc_mprime.wait(timeout=5)
  except subprocess.TimeoutExpired:
    proc_mprime.kill()
  set_apple_fan_speed('auto')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
