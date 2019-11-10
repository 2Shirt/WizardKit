"""WizardKit: Hardware diagnostics"""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib
import platform

from collections import OrderedDict
from docopt import docopt

from wk.cfg.main import KIT_NAME_FULL
from wk.exe import run_program
from wk.std import (
  Menu,
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


def main_menu():
  """Main menu for hardware diagnostics."""
  args = docopt(DOCSTRING)
  menu = Menu()

  # Build menu
  menu.title = color_string(
    strings=['Hardware Diagnostics', 'Main Menu'],
    colors=['GREEN', None],
    sep='\n',
    )
  for action in MENU_ACTIONS:
    menu.add_action(action)
  for option in MENU_OPTIONS:
    menu.add_option(option, {'Selected': True})
  for toggle in MENU_TOGGLES:
    menu.add_toggle(toggle, {'Selected': True})
  for name, targets in MENU_SETS.items():
    menu.add_set(name, {'Targets': targets})
  menu.actions['Start']['Separator'] = True

  # Check if running a quick check
  if args['--quick']:
    for name in menu.options.keys():
      # Only select quick option(s)
      menu.options[name]['Selected'] = name in MENU_OPTIONS_QUICK

  # Compatibility checks
  if platform.system() != 'Linux':
    for name in ('Audio Test', 'Keyboard Test', 'Network Test'):
      menu.actions[name]['Disabled'] = True

  # Show menu
  while True:
    selection = menu.advanced_select()
    if 'Audio Test' in selection:
      audio_test()
    elif 'Quit' in selection:
      break
    print(f'Sel: {selection}')
    print('')
    pause()


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
