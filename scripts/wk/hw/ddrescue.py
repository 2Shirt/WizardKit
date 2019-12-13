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

from wk import cfg, debug, exe, log, net, std, tmux
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
  f'Change settings {std.color_string("(experts only)", "YELLOW")}',
  'Quit')
MENU_TOGGLES = {
  'Auto continue (if recovery % over threshold)': True,
  'Retry (mark non-rescued sectors "non-tried")': False,
  'Reverse direction': False,
  }
PANE_RATIOS = (
  12, # SMART
  22, # ddrescue progress
  4,  # Journal (kernel messages)
  )
SETTING_PRESETS = (
  'Default',
  'Fast',
  'Safe',
  )
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
    self.block_pairs = []
    self.destination = None
    self.disks = []
    self.layout = cfg.ddrescue.TMUX_LAYOUT.copy()
    self.log_dir = None
    self.panes = {}
    self.source = None

    # Start a background process to maintain layout
    self.init_tmux()
    exe.start_thread(self.fix_tmux_layout_loop)

  def fix_tmux_layout(self, forced=True):
    # pylint: disable=unused-argument
    """Fix tmux layout based on cfg.ddrescue.TMUX_LAYOUT."""
    needs_fixed = tmux.layout_needs_fixed(self.panes, self.layout)

    # Main layout fix
    try:
      tmux.fix_layout(self.panes, self.layout, forced=forced)
    except RuntimeError:
      # Assuming self.panes changed while running
      pass

    # Source/Destination
    if forced or needs_fixed:
      self.update_top_panes()

    # SMART/Journal
    height = tmux.get_pane_size(self.panes['Progress'])[1] - 2
    p_ratios = [int((x/sum(PANE_RATIOS)) * height) for x in PANE_RATIOS]
    if 'SMART' in self.panes:
      tmux.resize_pane(self.panes['SMART'], height=p_ratios[0])
      tmux.resize_pane(height=p_ratios[1])
    if 'Journal' in self.panes:
      tmux.resize_pane(self.panes['Journal'], height=p_ratios[2])

  def fix_tmux_layout_loop(self):
    """Fix tmux layout on a loop.

    NOTE: This should be called as a thread.
    """
    while True:
      self.fix_tmux_layout(forced=False)
      std.sleep(1)

  def init_recovery(self, docopt_args):
    """Select source/dest and set env."""

    # Set log
    self.log_dir = log.format_log_path()
    self.log_dir = pathlib.Path(
      f'{self.log_dir.parent}/'
      f'ddrescue-TUI_{time.strftime("%Y-%m-%d_%H%M%S%z")}/'
      )
    log.update_log_path(
      dest_dir=self.log_dir,
      dest_name='main',
      keep_history=True,
      timestamp=False,
      )

    # Update progress pane
    tmux.respawn_pane(
      pane_id=self.panes['Progress'],
      watch_file=f'{self.log_dir}/progress.out',
      )

    # Set mode
    mode = set_mode(docopt_args)

    # Select source
    # TODO

    # Select destination
    # TODO

    # Update panes
    self.update_progress_pane()
    self.update_top_panes()

  def init_tmux(self):
    """Initialize tmux layout."""
    tmux.kill_all_panes()

    # Source (placeholder)
    self.panes['Source'] = tmux.split_window(
      behind=True,
      lines=2,
      text=' ',
      vertical=True,
      )

    # Started
    self.panes['Started'] = tmux.split_window(
      lines=cfg.ddrescue.TMUX_SIDE_WIDTH,
      target_id=self.panes['Source'],
      text=std.color_string(
        ['Started', time.strftime("%Y-%m-%d %H:%M %Z")],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Source / Dest
    self.update_top_panes()

    # Progress (placeholder)
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

  def update_top_panes(self):
    """(Re)create top source/destination panes."""
    width = tmux.get_pane_size()[0]
    width = int(width / 2) - 1

    # Kill destination pane
    if 'Destination' in self.panes:
      tmux.kill_pane(self.panes.pop('Destination'))

    # Source
    source_str = ' '
    if self.source:
      source_str = f'{self.source.path} {self.source.description}'
    if len(source_str) > width:
      source_str = f'{source_str[:width-3]}...'
    tmux.respawn_pane(
      self.panes['Source'],
      text=std.color_string(
        ['Source', source_str],
        ['BLUE', None],
        sep='\n',
        ),
      )

    # Destination
    dest_str = ''
    if self.destination:
      dest_str = f'{self.destination.path} {self.destination.description}'
    if len(dest_str) > width:
      if self.destination.path.is_dir():
        dest_str = f'...{dest_str[-width+3:]}'
      else:
        dest_str = f'{dest_str[:width-3]}...'
    self.panes['Destination'] = tmux.split_window(
      percent=50,
      vertical=False,
      target_id=self.panes['Source'],
      text=std.color_string(
        ['Destination', dest_str],
        ['BLUE', None],
        sep='\n',
        ),
      )


# Functions
def build_main_menu():
  """Build main menu, returns wk.std.Menu."""
  menu = std.Menu(title=std.color_string('ddrescue TUI: Main Menu', 'GREEN'))
  menu.separator = ' '

  # Add actions, options, etc
  for action in MENU_ACTIONS:
    menu.add_action(action)
  for toggle, selected in MENU_TOGGLES.items():
    menu.add_toggle(toggle, {'Selected': selected})

  # Done
  return menu


def build_settings_menu(silent=True):
  """Build settings menu, returns wk.std.Menu."""
  title_text = [
    std.color_string('ddrescue TUI: Exper Settings', 'GREEN'),
    ' ',
    std.color_string(
      ['These settings can cause', 'MAJOR DAMAGE', 'to drives'],
      ['YELLOW', 'RED', 'YELLOW'],
      ),
    'Please read the manual before making changes',
    ]
  menu = std.Menu(title='\n'.join(title_text))
  menu.separator = ' '
  preset = 'Default'
  if not silent:
    # Ask which preset to use
    print(f'Available ddrescue presets: {" / ".join(SETTING_PRESETS)}')
    preset = std.choice(SETTING_PRESETS, 'Please select a preset:')

    # Fix selection
    for _p in SETTING_PRESETS:
      if _p.startswith(preset):
        preset = _p

  # Add default settings
  menu.add_action('Main Menu')
  menu.add_action('Load Preset')
  for name, details in cfg.ddrescue.DDRESCUE_SETTINGS['Default'].items():
    menu.add_option(name, details.copy())

  # Update settings using preset
  if preset != 'Default':
    for name, details in cfg.ddrescue.DDRESCUE_SETTINGS[preset].items():
      menu.options[name].update(details.copy())

  # Done
  return menu


def main():
  """Main function for ddrescue TUI."""
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
  state.init_recovery(args)

  # Show menu
  while True:
    action = None
    selection = main_menu.advanced_select()

    # Change settings
    if 'Change settings' in selection[0]:
      while True:
        selection = settings_menu.settings_select()
        if 'Load Preset' in selection:
          # Rebuild settings menu using preset
          settings_menu = build_settings_menu(silent=False)
        else:
          break

    # Start recovery
    if 'Start' in selection:
      run_recovery(state, main_menu, settings_menu)

    # Quit
    if 'Quit' in selection:
      break


def run_recovery(state, main_menu, settings_menu):
  """Run recovery passes."""
  atexit.register(state.save_debug_reports)

  # Start SMART/Journal
  # TODO

  # TODO
  # Run ddrescue

  # Stop SMART/Journal
  # TODO

  # Done
  state.save_debug_reports()
  atexit.unregister(state.save_debug_reports)
  std.pause('Press Enter to return to main menu...')


def set_mode(docopt_args):
  """Set mode from docopt_args or user selection, returns str."""
  mode = None

  # Check docopt_args
  if docopt_args['clone']:
    mode = 'Clone'
  elif docopt_args['image']:
    mode = 'Image'

  # Ask user if necessary
  if not mode:
    answer = std.choice(['C', 'I'], 'Are we cloning or imaging?')
    if answer == 'C':
      mode = 'Clone'
    else:
      mode = 'Image'

  # Done
  return mode


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
