"""WizardKit: ddrescue TUI"""
# pylint: disable=too-many-lines
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

from wk import cfg, debug, exe, graph, log, net, std, tmux
from wk.hw import obj as hw_obj
from wk.hw import sensors as hw_sensors


# STATIC VARIABLES
DOCSTRING = f'''{cfg.main.KIT_NAME_FULL}: ddrescue TUI

Usage:
  ddrescue-tui
  ddrescue-tui (clone|image) [<source> [<destination>]]
  ddrescue-tui (-h | --help)

Options:
  -h --help           Show this page
'''
LOG = logging.getLogger(__name__)
MENU_ACTIONS = (
  'Start',
  std.color_string(['Change settings', '(experts only)'], [None, 'YELLOW']),
  'Quit')
MENU_TOGGLES = {
  'Auto continue (if recovery % over threshold)': True,
  'Retry (mark non-rescued sectors "non-tried")': False,
  'Reverse direction': False,
  }
STATUS_COLORS = {
  'Passed': 'GREEN',
  'Aborted': 'YELLOW',
  'Skipped': 'YELLOW',
  'Working': 'YELLOW',
  'ERROR': 'RED',
  }


# Classes
class State():
  """Object for tracking hardware diagnostic data."""
  def __init__(self):
    #TODO
    self.block_pairs = []
    self.disks = []
    self.layout = cfg.ddrescue.TMUX_LAYOUT.copy()
    self.log_dir = None
    self.panes = {}

    # Init tmux and start a background process to maintain layout
    self.init_tmux()
    exe.start_thread(self.fix_tmux_layout_loop)

  def fix_tmux_layout(self, forced=True):
    # pylint: disable=unused-argument
    """Fix tmux layout based on cfg.ddrescue.TMUX_LAYOUT."""
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

  def init_tmux(self):
    """Initialize tmux layout."""
    tmux.kill_all_panes()

    # Source / Dest
    self.update_top_panes()

    # Started
    self.panes['Started'] = tmux.split_window(
      lines=cfg.ddrescue.TMUX_SIDE_WIDTH,
      target_id=self.panes['Top'],
      text=std.color_string(
        ['Started', time.strftime("%Y-%m-%d %H:%M %Z")],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Progress
    self.panes['Progress'] = tmux.split_window(
      lines=cfg.ddrescue.TMUX_SIDE_WIDTH,
      text=' ',
      )

  def save_debug_reports(self):
    """Save debug reports to disk."""
    LOG.info('Saving debug reports')
    debug_dir = pathlib.Path(f'{self.log_dir}/debug')
    if not debug_dir.exists():
      debug_dir.mkdir()

    # State (self)
    with open(f'{debug_dir}/state.report', 'a') as _f:
      _f.write('\n'.join(debug.generate_object_report(self)))

    # Block pairs
    for _bp in self.block_pairs:
      with open(f'{debug_dir}/bp_part#.report', 'a') as _f:
        _f.write('\n'.join(debug.generate_object_report(_bp)))

  def update_progress_pane(self):
    """Update progress pane."""
    report = []
    width = cfg.ddrescue.TMUX_SIDE_WIDTH

    #TODO

    # Write to progress file
    out_path = pathlib.Path(f'{self.log_dir}/progress.out')
    with open(out_path, 'w') as _f:
      _f.write('\n'.join(report))

  def update_top_panes(self, text):
    """(Re)create top source/destination panes."""
    #TODO
    self.panes['Source'] = tmux.split_window(
      behind=True,
      lines=2,
      vertical=True,
      text=std.color_string(
        ['Source', f'TODO'],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Destination
    self.panes['Destination'] = tmux.split_window(
      percent=50,
      vertical=False,
      target_id=self.panes['Source'],
      text=std.color_string(
        ['Destination', f'TODO'],
        ['BLUE', None],
        sep='\n',
        ),
      )


# Functions
def build_main_menu():
  """Build main menu, returns wk.std.Menu."""
  menu = std.Menu(title=std.color_string('ddrescue TUI: Main Menu', 'GREEN'))

  # Add actions, options, etc
  for action in MENU_ACTIONS:
    menu.add_action(action)
  for toggle, selected in MENU_TOGGLES.items():
    menu.add_toggle(toggle, {'Selected': selected})
  menu.actions['Start']['Separator'] = True

  # Done
  return menu


def build_settings_menu():
  """Build settings menu, returns wk.std.Menu."""
  #TODO Fixme
  title_text = [
    std.color_string('ddrescue TUI: Exper Settings', 'GREEN'),
    ' ',
    std.color_string(
      ['These settings can cause', 'MAJOR DAMAGE', 'to drives'],
      ['YELLOW', 'RED', 'YELLOW'],
      ),
    'Please read the manual before making changes',
    ]
  menu = std.Menu(title='\n'join(title_text))

  # Add actions, options, etc
  menu.add_action('Main Menu')
  for name, details in cfg.ddrescue.DDRESCUE_SETTINGS.items():
    menu.add_option(name, details)
  menu.actions['Main Menu']['Separator'] = True

  # Done
  return menu


def main():
  # pylint: disable=too-many-branches
  """Main function for hardware diagnostics."""
  args = docopt(DOCSTRING)
  log.update_log_path(dest_name='ddrescue-TUI', timestamp=True)

  # Safety check
  if 'TMUX' not in os.environ:
    LOG.error('tmux session not found')
    raise RuntimeError('tmux session not found')

  # Init
  atexit.register(tmux.kill_all_panes)
  main_menu = build_main_menu()
  settings_menu = build_settings_menu()
  state = State()

  # Show menu
  while True:
    action = None
    selection = menu.advanced_select()

    # Start diagnostics
    if 'Start' in selection:
      run_diags(state, menu, quick_mode=False)

    # Quit
    if 'Quit' in selection:
      break


def run_recovery(state, main_menu, settings_menu):
  """Run recovery passes."""
  aborted = False
  atexit.register(state.save_debug_reports)
  state.init_recovery(menu)

  # TODO
  # Run ddrescue

  # Done
  state.save_debug_reports()
  atexit.unregister(state.save_debug_reports)
  std.pause('Press Enter to return to main menu...')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
