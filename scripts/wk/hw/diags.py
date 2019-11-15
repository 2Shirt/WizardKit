"""WizardKit: Hardware diagnostics"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
import platform
import plistlib
import re
import subprocess
import time

from collections import OrderedDict
from docopt import docopt

from wk import cfg, exe, log, net, std, tmux
from wk.hw import obj as hw_obj
from wk.hw import sensors as hw_sensors


# atexit functions
atexit.register(tmux.kill_all_panes)
#TODO: Add state/dev data dump debug function

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
WK_LABEL_REGEX = re.compile(
  fr'{cfg.main.KIT_NAME_SHORT}_(LINUX|UFD)',
  re.IGNORECASE,
  )


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
    #TODO: Fix SIGWINCH?
    #if hasattr(signal, 'SIGWINCH'):
    #  # Use signal handling
    #  signal.signal(signal.SIGWINCH, self.fix_tmux_layout)
    #else:
    #  exe.start_thread(self.fix_tmux_layout_loop)
    exe.start_thread(self.fix_tmux_layout_loop)

  def fix_tmux_layout(self, forced=True, signum=None, frame=None):
    # pylint: disable=unused-argument
    """Fix tmux layout based on cfg.hw.TMUX_LAYOUT.

    NOTE: To support being called by both a signal and a thread
          signum and frame must be valid aguments.
    """
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
    std.print_info('Starting Hardware Diagnostics')

    # Add HW Objects
    self.cpu = hw_obj.CpuRam()
    self.disks = get_disks()

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
        self.cpu.tests[name] = test_mprime_obj
        self.cpu.tests[name] = test_cooling_obj
        self.tests[name]['Objects'].append(test_mprime_obj)
        self.tests[name]['Objects'].append(test_cooling_obj)
      elif 'Disk' in name:
        for disk in self.disks:
          test_obj = hw_obj.Test(dev=disk, label=disk.path.name)
          disk.tests[name] = test_obj
          self.tests[name]['Objects'].append(test_obj)

        # No disks detected?
        if not self.tests[name]['Objects']:
          test_obj = hw_obj.Test(dev=None, label='')
          test_obj.set_status('N/A')
          test_obj.disabled = True
          self.tests[name]['Objects'].append(test_obj)

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

  def update_top_pane(self, text):
    """Update top pane with text."""
    tmux.respawn_pane(self.panes['Top'], text=f'{self.top_text}\n{text}')


# Functions
def audio_test():
  """Run an OS-specific audio test."""
  if platform.system() == 'Linux':
    audio_test_linux()
  # TODO: Add tests for other OS


def audio_test_linux():
  """Run an audio test using amixer and speaker-test."""
  LOG.info('Audio Test')
  std.clear_screen()

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
  if platform.system() != 'Linux':
    for name in ('Audio Test', 'Keyboard Test', 'Network Test'):
      menu.actions[name]['Disabled'] = True
  if platform.system() not in ('Darwin', 'Linux'):
    for name in ('Matrix', 'Tubes'):
      menu.actions[name]['Disabled'] = True

  # Done
  return menu


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


def cpu_mprime_test(state, test_objects):
  """CPU & cooling check using Prime95."""
  LOG.info('CPU Test (Prime95)')
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
  sensors.start_background_monitor(sensors_out)

  # Create monitor and worker panes
  state.panes['Prime95'] = tmux.split_window(
    lines=10, vertical=True, watch_file=prime_log)
  state.panes['Temps'] = tmux.split_window(
    behind=True, percent=80, vertical=True, watch_file=sensors_out)
  tmux.resize_pane(height=3)
  state.panes['Current'] = ''
  state.layout['Current'] = {'height': 3, 'Check': True}

  # Get idle temps
  std.clear_screen()
  std.print_standard('Saving idle temps...')
  sensors.save_average_temps(temp_label='Idle', seconds=5)

  # Stress CPU
  std.print_info('Starting stress test')
  std.print_warning('If running too hot, press CTRL+c to abort the test')
  set_apple_fan_speed('max')
  proc_mprime = start_mprime_thread(state.log_dir, prime_log)

  # Show countdown
  try:
    print_countdown(seconds=cfg.hw.CPU_TEST_MINUTES*60)
  except KeyboardInterrupt:
    test_cooling_obj.set_status('Aborted')
    test_mprime_obj.set_status('Aborted')
  except hw_sensors.ThermalLimitReachedError:
    test_mprime_obj.set_status('Aborted')

  # Stop Prime95
  proc_mprime.terminate()
  try:
    proc_mprime.wait(timeout=5)
  except subprocess.TimeoutExpired:
    proc_mprime.kill()
  set_apple_fan_speed('auto')

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
  sensors.stop_background_monitor()
  state.panes.pop('Current', None)
  tmux.kill_pane(state.panes.pop('Prime95', None))
  tmux.kill_pane(state.panes.pop('Temps', None))


def disk_attribute_check(state, test_objects):
  """Disk attribute check."""
  LOG.info('Disk Attribute Check')
  #TODO: at
  std.print_warning('TODO: at')
  std.pause()


def disk_io_benchmark(state, test_objects):
  """Disk I/O benchmark using dd."""
  LOG.info('Disk I/O Benchmark (dd)')
  #TODO: io
  std.print_warning('TODO: io')
  std.pause()


def disk_self_test(state, test_objects):
  """Disk self-test if available."""
  LOG.info('Disk Self-Test')
  #TODO: st
  std.print_warning('TODO: st')
  std.pause()


def disk_surface_scan(state, test_objects):
  """Disk surface scan using badblocks."""
  LOG.info('Disk Surface Scan (badblocks)')
  #TODO: bb
  std.print_warning('TODO: bb')
  std.pause()


def get_disks():
  """Get disks using OS-specific methods, returns list."""
  disks = []
  if platform.system() == 'Darwin':
    disks = get_disks_macos()
  elif platform.system() == 'Linux':
    disks = get_disks_linux()

  # Done
  return disks


def get_disks_linux():
  """Get disks via lsblk, returns list."""
  cmd = ['lsblk', '--json', '--nodeps', '--paths']
  disks = []

  # Add valid disks
  json_data = exe.get_json_from_command(cmd)
  for disk in json_data.get('blockdevices', []):
    disk_obj = hw_obj.Disk(disk['name'])
    skip = False

    # Skip loopback devices, optical devices, etc
    if disk_obj.details['type'] != 'disk':
      skip = True

    # Skip WK disks
    for label in disk_obj.get_labels():
      if WK_LABEL_REGEX.search(label):
        skip = True

    # Add disk
    if not skip:
      disks.append(disk_obj)

  # Done
  return disks


def get_disks_macos():
  """Get disks via diskutil, returns list."""
  cmd = ['diskutil', 'list', '-plist', 'physical']
  disks = []

  # Get info from diskutil
  proc = exe.run_program(cmd, encoding=None, errors=None)
  try:
    plist_data = plistlib.loads(proc.stdout)
  except (TypeError, ValueError):
    # Invalid / corrupt plist data? return empty list to avoid crash
    LOG.error('Failed to get diskutil list')
    return disks

  # Add valid disks
  for disk in plist_data['WholeDisks']:
    disk_obj = hw_obj.Disk(f'/dev/{disk}')
    skip = False

    # Skip WK disks
    for label in disk_obj.get_labels():
      if WK_LABEL_REGEX.search(label):
        skip = True

    # Add disk
    if not skip:
      disks.append(disk_obj)

  # Done
  return disks


def keyboard_test():
  """Test keyboard using xev."""
  LOG.info('Keyboard Test (xev)')
  cmd = ['xev', '-event', 'keyboard']
  std.clear_screen()
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
  menu = build_menu(cli_mode=args['--cli'], quick_mode=args['--quick'])
  state = State()

  # Quick Mode
  if args['--quick']:
    std.clear_screen()
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
    if 'Quit' in selection:
      break
    elif 'Reboot' in selection:
      cmd = ['/usr/local/bin/wk-power-command', 'reboot']
      exe.run_program(cmd, check=False)
    elif 'Power Off' in selection:
      cmd = ['/usr/local/bin/wk-power-command', 'poweroff']
      exe.run_program(cmd, check=False)

    # Start diagnostics
    if 'Start' in selection:
      run_diags(state, menu, quick_mode=False)

    # Reset top pane
    state.update_top_pane('Main Menu')


def network_test():
  """Run network tests."""
  LOG.info('Network Test')
  std.clear_screen()
  try_and_print = std.TryAndPrint()
  result = try_and_print.run(
    'Network connection...', net.connected_to_private_network, msg_good='OK')

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


def print_countdown(seconds):
  """Print countdown to screen."""
  for i in range(seconds):
    sec_left = (seconds - i) % 60
    min_left = int((seconds - i) / 60)

    out_str = '\r  '
    if min_left:
      out_str += f'{min_left} minute{"s" if min_left != 1 else ""}, '
    out_str += f'{sec_left} second{"s" if sec_left != 1 else ""}'
    out_str += ' remaining'

    print(f'{out_str:<42}', end='', flush=True)
    std.sleep(1)

  # Done
  print('')


def run_diags(state, menu, quick_mode=False):
  """Run selected diagnostics."""
  aborted = False
  state.init_diags(menu)

  # Just return if no tests were selected
  if not any([details['Enabled'] for details in state.tests.values()]):
    std.print_warning('No tests selected?')
    std.pause()
    return

  # Run tests
  for details in state.tests.values():
    if not details['Enabled']:
      # Skip disabled tests
      continue

    # Run test(s)
    function = details['Function']
    try:
      function(state, details['Objects'])
    except std.GenericAbort:
      aborted = True
      # Restart tmux
      state.init_tmux()
      break

  # Handle aborts
  if aborted:
    for details in state.tests.values():
      for test_obj in details['Objects']:
        if test_obj.status == 'Pending':
          test_obj.set_status('Aborted')

  # Show results
  show_results(state)

  # Done
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
      'pipes' if platform.system() == 'Linux' else 'pipes.sh',
      '-t', '0',
      '-t', '1',
      '-t', '2',
      '-t', '3',
      '-t', '5',
      '-R', '-r', '4000',
      ]

  # Switch pane to fullscreen and start screensaver
  tmux.zoom_pane()
  exe.run_program(cmd, check=False, pipe=False)
  tmux.zoom_pane()


def set_apple_fan_speed(speed):
  """Set Apple fan speed."""
  cmd = None

  # Check
  if speed not in ('auto', 'max'):
    raise RuntimeError(f'Invalid speed {speed}')

  # Set cmd
  if platform.system() == 'Linux':
    cmd = ['apple-fans', speed]
  #TODO: Add method for use under macOS

  # Run cmd
  if cmd:
    exe.run_program(cmd, check=False)


def show_results(state):
  """Show test results by device."""
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


def start_mprime_thread(working_dir, log_path):
  """Start mprime and save filtered output to log, returns Popen object."""
  proc_mprime = subprocess.Popen(
    ['mprime', '-t'],
    bufsize=1,
    cwd=working_dir,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    )
  proc_grep = subprocess.Popen(
    'grep --ignore-case --invert-match --line-buffered stress.txt'.split(),
    bufsize=1,
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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
