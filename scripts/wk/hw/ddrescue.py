"""WizardKit: ddrescue TUI"""
# pylint: disable=too-many-lines
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import pathlib
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
PLATFORM = std.PLATFORM
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
    if 'Progress' not in self.panes:
      # Assumning we're still selecting source/dest
      return
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
    std.clear_screen()

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

    # Set mode
    mode = set_mode(docopt_args)

    # Select source
    self.source = get_object(docopt_args['<source>'])
    if not self.source:
      self.source = select_disk('Source')
    source_parts = select_disk_parts(mode, self.source)
    self.update_top_panes()
    std.pause()

    # Select destination
    self.destination = get_object(docopt_args['<destination>'])
    if not self.destination:
      if mode == 'Clone':
        self.destination = select_disk('Destination', self.source)
      elif mode == 'Image':
        self.destination = select_path('Destination')
    self.update_top_panes()

    # Update panes
    self.panes['Progress'] = tmux.split_window(
      lines=cfg.ddrescue.TMUX_SIDE_WIDTH,
      watch_file=f'{self.log_dir}/progress.out',
      )
    self.update_progress_pane()

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

    def _format_string(obj, width):
      """Format source/dest string using obj and width, returns str."""
      string = ''

      # Build base string
      if isinstance(obj, hw_obj.Disk):
        string = f'{obj.path} {obj.description}'
      elif obj.is_dir():
        string = f'{obj}/'
      elif obj.is_file():
        size_str = std.bytes_to_string(
          obj.stat().st_size,
          decimals=0,
          use_binary=False)
        string = f'{obj.name} {size_str}'

      # Adjust for width
      if len(string) > width:
        if hasattr(obj, 'is_dir') and obj.is_dir():
          string = f'...{string[-width+3:]}'
        else:
          string = f'{string[:width-3]}...'

      # Done
      return string

    # Kill destination pane
    if 'Destination' in self.panes:
      tmux.kill_pane(self.panes.pop('Destination'))

    # Source
    source_str = ' '
    if self.source:
      source_str = _format_string(self.source, width)
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
      dest_str = _format_string(self.destination, width)
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
    std.color_string('ddrescue TUI: Expert Settings', 'GREEN'),
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


def get_object(path):
  """Get object based on path, returns obj."""
  obj = None

  # Bail early
  if not path:
    return obj

  # Check path
  path = pathlib.Path(path).resolve()
  if path.is_block_device() or path.is_char_device():
    obj = hw_obj.Disk(path)

    # Child/Parent check
    parent = obj.details['parent']
    if parent:
      std.print_warning(f'"{obj.path}" is a child device')
      if std.ask(f'Use parent device "{parent}" instead?'):
        obj = hw_obj.Disk(parent)
  elif path.is_dir():
    obj = path
  elif path.is_file():
    # Assuming file is a raw image, mounting
    loop_path = mount_raw_image(path)
    obj = hw_obj.Disk(loop_path)

  # Abort if obj not set
  if not obj:
    std.print_error(f'Invalid source/dest path: {path}')
    raise std.GenericAbort()

  # Done
  return obj


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
  try:
    state.init_recovery(args)
  except std.GenericAbort:
    std.abort()

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


def mount_raw_image(path):
  """Mount raw image using OS specific methods, returns pathlib.Path."""
  loopback_path = None

  if PLATFORM == 'Darwin':
    loopback_path = mount_raw_image_macos(path)
  elif PLATFORM == 'Linux':
    loopback_path = mount_raw_image_linux(path)

  # Check
  if not loopback_path:
    std.print_error(f'Failed to mount image: {path}')

  # Register unmount atexit
  atexit.register(unmount_loopback_device, loopback_path)

  # Done
  return loopback_path


def mount_raw_image_linux(path):
  """Mount raw image using losetup, returns pathlib.Path."""
  loopback_path = None

  # Mount using losetup
  cmd = [
    'sudo',
    'losetup',
    '--find',
    '--partscan',
    '--show',
    path,
    ]
  proc = exe.run_program(cmd, check=False)

  # Check result
  if proc.returncode == 0:
    loopback_path = proc.stdout.strip()

  # Done
  return loopback_path

def mount_raw_image_macos(path):
  """Mount raw image using hdiutil, returns pathlib.Path."""
  loopback_path = None
  plist_data = {}

  # Mount using hdiutil
  # plistdata['system-entities'][{}...]
  cmd = [
    'hdiutil', 'attach',
    '-imagekey', 'diskimage-class=CRawDiskImage',
    '-nomount',
    '-plist',
    '-readonly',
    path,
    ]
  proc = exe.run_program(cmd, check=False, encoding=None, errors=None)

  # Check result
  try:
    plist_data = plistlib.loads(proc.stdout)
  except plistlib.InvalidFileException:
    return None
  for dev in plist_data.get('system-entities', []):
    dev_path = dev.get('dev-entry', '')
    if re.match(r'^/dev/disk\d+$', dev_path):
      loopback_path = dev_path

  # Done
  return loopback_path


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


def select_disk(prompt, skip_disk=None):
  """Select disk from list, returns Disk()."""
  std.print_info('Scanning disks...')
  disks = hw_obj.get_disks()
  menu = std.Menu(
    title=std.color_string(f'ddrescue TUI: {prompt} Selection', 'GREEN'),
    )
  menu.disabled_str = 'Already selected'
  menu.separator = ' '
  menu.add_action('Quit')
  for disk in disks:
    disable_option = False
    size = disk.details["size"]

    # Check if option should be disabled
    if skip_disk:
      parent = skip_disk.details.get('parent', None)
      if (disk.path.samefile(skip_disk.path)
          or (parent and disk.path.samefile(parent))):
        disable_option = True

    # Add to menu
    menu.add_option(
      name=(
        f'{str(disk.path):<12} '
        f'{disk.details["bus"]:<5} '
        f'{std.bytes_to_string(size, decimals=1, use_binary=False):<8} '
        f'{disk.details["model"]} '
        f'{disk.details["serial"]}'
        ),
      details={'Disabled': disable_option, 'Object': disk},
      )

  # Get selection
  selection = menu.simple_select()
  if 'Quit' in selection:
    raise std.GenericAbort()

  # Done
  return selection[-1]['Object']


def select_disk_parts(prompt, disk):
  """Select disk parts from list, returns list of Disk()."""
  title = std.color_string(f'ddrescue TUI: Partition Selection', 'GREEN')
  title += f'\n\nDisk: {disk.path} {disk.description}'
  menu = std.Menu(title)
  menu.separator = ' '
  menu.add_action('All')
  menu.add_action('None')
  menu.add_action('Proceed', {'Separator': True})
  menu.add_action('Quit')
  object_list = []

  # Bail early if child device selected
  if disk.details.get('parent', False):
    return [disk]

  # Add parts
  whole_disk_str = f'{str(disk.path):<14} (Whole device)'
  for part in disk.details.get('children', []):
    size = part["size"]
    name = (
      f'{str(part["path"]):<14} '
      f'({std.bytes_to_string(size, decimals=1, use_binary=False):>6})'
      )
    menu.add_option(name, details={'Selected': True, 'Path': part['path']})

  # Add whole disk if necessary
  if not menu.options:
    menu.add_option(whole_disk_str, {'Selected': True, 'Path': disk.path})
    menu.title += '\n\n'
    menu.title += std.color_string(' No partitions detected.', 'YELLOW')

  # Get selection
  while True:
    selection = menu.advanced_select(
      f'Please select the parts to {prompt.lower()}: ',
      )
    if 'All' in selection:
      for option in menu.options.values():
        option['Selected'] = True
    elif 'None' in selection:
      for option in menu.options.values():
        option['Selected'] = False
    elif 'Proceed' in selection:
      if any([option['Selected'] for option in menu.options.values()]):
        # At least one partition/device selected/device selected
        break
    elif 'Quit' in selection:
      raise std.GenericAbort()

  # Build list of Disk() object_list
  for option in menu.options.values():
    if option['Selected']:
      object_list.append(option['Path'])

  # Check if whole disk selected
  if len(object_list) == len(disk.details.get('children', [])):
    # NOTE: This is not true if the disk has no partitions
    msg = f'Preserve partition table and unused space in {prompt.lower()}?'
    if std.ask(msg):
      # Replace part list with whole disk obj
      object_list = [disk.path]

  # Convert object_list to hw_obj.Disk() objects
  print(' ')
  std.print_info('Getting disk/partition details...')
  object_list = [hw_obj.Disk(path) for path in object_list]

  # Done
  return object_list


def select_path(prompt):
  """Select path, returns pathlib.Path."""
  invalid = False
  menu = std.Menu(
    title=std.color_string(f'ddrescue TUI: {prompt} Path Selection', 'GREEN'),
    )
  menu.separator = ' '
  menu.add_action('Quit')
  menu.add_option(f'Current directory')
  menu.add_option('Enter manually')
  path = None

  # Make selection
  selection = menu.simple_select()
  if 'Current directory' in selection:
    path = os.getcwd()
  elif 'Enter manually' in selection:
    path = std.input_text('Please enter path: ')
  elif 'Quit' in selection:
    raise std.GenericAbort()

  # Check
  try:
    path = pathlib.Path(path).resolve()
  except TypeError:
    invalid = True
  if invalid or not path.is_dir():
    std.print_error(f'Invalid path: {path}')
    raise std.GenericAbort()

  # Done
  return path


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


def unmount_loopback_device(path):
  """Unmount loopback device using OS specific methods."""
  cmd = []

  # Build OS specific cmd
  if PLATFORM == 'Darwin':
    cmd = ['hdiutil', 'detach', path]
  elif PLATFORM == 'Linux':
    cmd = ['sudo', 'losetup', '--detach', path]

  # Unmount loopback device
  exe.run_program(cmd, check=False)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
