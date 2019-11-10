"""WizardKit: Hardware diagnostics"""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import platform

from collections import OrderedDict
from docopt import docopt

from wk.cfg.main import KIT_NAME_FULL
from wk.exe import run_program
from wk.net import (
  connected_to_private_network,
  ping,
  show_valid_addresses,
  speedtest,
  )
from wk.std import (
  Menu,
  TryAndPrint,
  clear_screen,
  color_string,
  pause,
  print_error,
  print_info,
  print_standard,
  print_warning,
  sleep,
  )


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
MENU_TOGGLES = []


# Classes
class State():
  """Object for tracking hardware diagnostic data."""
  def __init__(self):
    self.tests = OrderedDict()


# Functions
def audio_test():
  """Run an OS-specific audio test."""
  if platform.system() == 'Linux':
    audio_test_linux()
  # TODO: Add tests for other OS


def audio_test_linux():
  """Run an audio test using amixer and speaker-test."""
  clear_screen()
  print_standard('Audio test')
  print_standard('')

  # Set volume
  for source in ('Master', 'PCM'):
    cmd = f'amixer -q set "{source}" 80% unmute'.split()
    run_program(cmd, check=False)

  # Run audio tests
  for mode in ('pink', 'wav'):
    cmd = f'speaker-test -c 2 -l 1 -t {mode}'.split()
    run_program(cmd, check=False, pipe=False)


def build_menu(quick_mode=False):
  """Build main menu, returns wk.std.Menu."""
  menu = Menu()

  # Set title
  menu.title = color_string(
    strings=['Hardware Diagnostics', 'Main Menu'],
    colors=['GREEN', None],
    sep='\n',
    )

  # Add actions, options, etc
  for action in MENU_ACTIONS:
    menu.add_action(action)
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

  # Done
  return menu


def keyboard_test():
  """Test keyboard using xev."""
  cmd = ['xev', '-event', 'keyboard']
  clear_screen()
  run_program(cmd, check=False, pipe=False)


def main_menu():
  """Main menu for hardware diagnostics."""
  args = docopt(DOCSTRING)
  menu = build_menu(args['--quick'])

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
      try:
        action()
      except KeyboardInterrupt:
        print_warning('Aborted.')
        print_standard('')
        pause('Press Enter to return to main menu...')

    # Quit
    if 'Quit' in selection:
      break

    # Start diagnostics
    if 'Start' in selection:
      #TODO
      #run_diags()
      pass


def network_test():
  """Run network tests."""
  clear_screen()
  try_and_print = TryAndPrint()
  result = try_and_print.run(
    'Network connection...', connected_to_private_network, msg_good='OK')

  # Bail if not connected
  if result['Failed']:
    print_warning('Please connect to a network and try again')
    pause('Press Enter to return to main menu...')
    return

  # Show IP address(es)
  show_valid_addresses()

  # Ping tests
  try_and_print.run(
    'Internet connection...', ping, msg_good='OK', addr='8.8.8.8')
  try_and_print.run(
    'DNS resolution...', ping, msg_good='OK', addr='google.com')

  # Speedtest
  try_and_print.run('Speedtest...', speedtest)

  # Done
  pause('Press Enter to return to main menu...')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
