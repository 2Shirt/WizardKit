"""WizardKit: Hardware diagnostics"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import pathlib
import platform
import time

from collections import OrderedDict
from docopt import docopt

from wk import exe, net, std, tmux
from wk.cfg.hw import TMUX_SIDE_WIDTH
from wk.cfg.main import KIT_NAME_FULL


# atexit functions
atexit.register(tmux.kill_all_panes)

# STATIC VARIABLES
DOCSTRING = f'''{KIT_NAME_FULL}: Hardware Diagnostics

Usage:
  hw-diags
  hw-diags (-q | --quick)
  hw-diags (-h | --help)

Options:
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


# Classes
class State():
  """Object for tracking hardware diagnostic data."""
  def __init__(self):
    self.cpu = None
    self.disks = []
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
    self.init_tmux()

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
      lines=TMUX_SIDE_WIDTH,
      target_id=self.panes['Top'],
      text=std.color_string(
        ['Started', time.strftime("%Y-%m-%d %H:%M %Z")],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Progress
    self.panes['Progress'] = tmux.split_window(
      lines=TMUX_SIDE_WIDTH,
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
  std.clear_screen()

  # Set volume
  for source in ('Master', 'PCM'):
    cmd = f'amixer -q set "{source}" 80% unmute'.split()
    exe.run_program(cmd, check=False)

  # Run audio tests
  for mode in ('pink', 'wav'):
    cmd = f'speaker-test -c 2 -l 1 -t {mode}'.split()
    exe.run_program(cmd, check=False, pipe=False)


def build_menu(quick_mode=False):
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
  #TODO: p95
  std.print_warning('TODO: p95')


def disk_attribute_check():
  """Disk attribute check."""
  #TODO: at
  std.print_warning('TODO: at')


def disk_io_benchmark():
  """Disk I/O benchmark using dd."""
  #TODO: io
  std.print_warning('TODO: io')


def disk_self_test():
  """Disk self-test if available."""
  #TODO: st
  std.print_warning('TODO: st')


def disk_surface_scan():
  """Disk surface scan using badblocks."""
  #TODO: bb
  std.print_warning('TODO: bb')


def keyboard_test():
  """Test keyboard using xev."""
  cmd = ['xev', '-event', 'keyboard']
  std.clear_screen()
  exe.run_program(cmd, check=False, pipe=False)


def main():
  """Main function for hardware diagnostics."""
  args = docopt(DOCSTRING)
  menu = build_menu(args['--quick'])
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

    # Start diagnostics
    if 'Start' in selection:
      #TODO
      #run_diags()
      pass

    # Reset top pane
    state.update_top_pane('Main Menu')


def network_test():
  """Run network tests."""
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


def screensaver(name):
  """Show screensaver"""
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
