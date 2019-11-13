"""WizardKit: Hardware diagnostics"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
import platform
import plistlib
import re
import signal
import time

from collections import OrderedDict
from docopt import docopt

from wk import cfg, exe, log, net, std, tmux
from wk.hw import obj as hw_obj


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
    if hasattr(signal, 'SIGWINCH'):
      # Use signal handling
      signal.signal(signal.SIGWINCH, self.fix_tmux_layout)
    else:
      exe.start_thread(self.fix_tmux_layout_loop)

  def fix_tmux_layout(self, forced=True, signum=None, frame=None):
    # pylint: disable=unused-argument
    """Fix tmux layout based on cfg.hw.TMUX_LAYOUT.

    NOTE: To support being called by both a signal and a thread
          signum and frame must be valid aguments.
    """
    try:
      tmux.fix_layout(self.panes, cfg.hw.TMUX_LAYOUT, forced=forced)
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

  def init_diags(self):
    """Initialize diagnostic pass."""
    # Reset objects
    self.disks.clear()
    for test_data in self.tests.values():
      test_data['Objects'].clear()

    # Set log
    self.log_dir = log.format_log_path()
    self.log_dir = pathlib.Path(
      f'{self.log_dir.parent}/'
      f'Hardware-Diagnostics_{time.strftime("%Y-%m-%d_%H%M%z")}/'
      )
    log.update_log_path(
      dest_dir=self.log_dir,
      dest_name='main',
      keep_history=False,
      timestamp=False,
      )
    std.print_info('Starting Hardware Diagnostics')

    # Add CPU
    self.cpu = hw_obj.CpuRam()

    # Add disks
    self.disks = get_disks()

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
    for name in menu.options.keys():
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


def cpu_mprime_test():
  """CPU & cooling check using Prime95."""
  LOG.info('CPU Test (Prime95)')
  #TODO: p95
  std.print_warning('TODO: p95')


def disk_attribute_check():
  """Disk attribute check."""
  LOG.info('Disk Attribute Check')
  #TODO: at
  std.print_warning('TODO: at')


def disk_io_benchmark():
  """Disk I/O benchmark using dd."""
  LOG.info('Disk I/O Benchmark (dd)')
  #TODO: io
  std.print_warning('TODO: io')


def disk_self_test():
  """Disk self-test if available."""
  LOG.info('Disk Self-Test')
  #TODO: st
  std.print_warning('TODO: st')


def disk_surface_scan():
  """Disk surface scan using badblocks."""
  LOG.info('Disk Surface Scan (badblocks)')
  #TODO: bb
  std.print_warning('TODO: bb')


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
      #TODO
      #run_diags()
      pass

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


def run_diags(state):
  """Run selected diagnostics."""


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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
