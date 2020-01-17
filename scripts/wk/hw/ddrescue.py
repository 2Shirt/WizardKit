"""WizardKit: ddrescue TUI"""
# pylint: disable=too-many-lines
# vim: sts=2 sw=2 ts=2

import atexit
import datetime
import json
import logging
import math
import os
import pathlib
import plistlib
import re
import shutil
import subprocess
import time

from collections import OrderedDict
from docopt import docopt

import psutil
import pytz

from wk import cfg, debug, exe, io, log, net, std, tmux
from wk.hw import obj as hw_obj


# STATIC VARIABLES
DOCSTRING = f'''{cfg.main.KIT_NAME_FULL}: ddrescue TUI

Usage:
  ddrescue-tui
  ddrescue-tui [options] (clone|image) [<source> [<destination>]]
  ddrescue-tui (-h | --help)

Options:
  -h --help           Show this page
  -s --dry-run        Print commands to be used instead of running them
  --force-local-map   Skip mounting shares and save map to local drive
  --start-fresh       Ignore previous runs and start new recovery
'''
CLONE_SETTINGS = {
  'Source': None,
  'Destination': None,
  'Create Boot Partition': False,
  'First Run': True,
  'Needs Format': False,
  'Table Type': None,
  'Partition Mapping': [
    # (5, 1) ## Clone source partition #5 to destination partition #1
    ],
  }
DDRESCUE_LOG_REGEX = re.compile(
  r'^\s*(?P<key>\S+):\s+'
  r'(?P<size>\d+)\s+'
  r'(?P<unit>[PTGMKB]i?B?)'
  r'.*\(\s*(?P<percent>\d+\.?\d*)%\)$',
  re.IGNORECASE,
  )
REGEX_REMAINING_TIME = re.compile(
  r'remaining time:'
  r'\s*((?P<days>\d+)d)?'
  r'\s*((?P<hours>\d+)h)?'
  r'\s*((?P<minutes>\d+)m)?'
  r'\s*((?P<seconds>\d+)s)?'
  r'\s*(?P<na>n/a)?',
  re.IGNORECASE
  )
LOG = logging.getLogger(__name__)
MENU_ACTIONS = (
  'Start',
  f'Change settings {std.color_string("(experts only)", "YELLOW")}',
  'Quit')
MENU_TOGGLES = {
  'Auto continue (if recovery % over threshold)': True,
  'Retry (mark non-rescued sectors "non-tried")': False,
  }
PANE_RATIOS = (
  12, # SMART
  22, # ddrescue progress
  4,  # Journal (kernel messages)
  )
PLATFORM = std.PLATFORM
RECOMMENDED_FSTYPES = re.compile(r'^(ext[234]|ntfs|xfs)$')
RECOMMENDED_MAP_FSTYPES = re.compile(r'^(cifs|ext[234]|ntfs|vfat|xfs)$')
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
TIMEZONE = pytz.timezone(cfg.main.LINUX_TIME_ZONE)


# Classes
class BlockPair():
  """Object for tracking source to dest recovery data."""
  def __init__(self, source, destination, model, working_dir):
    """Initialize BlockPair()

    NOTE: source should be a wk.hw.obj.Disk() object
          and destination should be a pathlib.Path() object.
    """
    self.source = source.path
    self.destination = destination
    self.map_data = {}
    self.map_path = None
    self.size = source.details['size']
    self.status = OrderedDict({
      'read': 'Pending',
      'trim': 'Pending',
      'scrape': 'Pending',
      })

    # Set map file
    # e.g. '(Clone|Image)_Model[_p#]_Size[_Label].map'
    map_name = model if model else 'None'
    if source.details['bus'] == 'Image':
      map_name = 'Image'
    if source.details['parent']:
      part_num = re.sub(r"^.*?(\d+)$", r"\1", source.path.name)
      map_name += f'_p{part_num}'
    size_str = std.bytes_to_string(
      size=source.details["size"],
      use_binary=False,
      )
    map_name += f'_{size_str.replace(" ", "")}'
    if source.details.get('label', ''):
      map_name += f'_{source.details["label"]}'
    map_name = map_name.replace(' ', '_')
    map_name = map_name.replace('/', '_')
    if destination.is_dir():
      # Imaging
      self.map_path = pathlib.Path(f'{destination}/Image_{map_name}.map')
      self.destination = self.map_path.with_suffix('.dd')
      self.destination.touch()
    else:
      # Cloning
      self.map_path = pathlib.Path(f'{working_dir}/Clone_{map_name}.map')
    self.map_path.touch()

    # Set initial status
    self.set_initial_status()

  def get_error_size(self):
    """Get error size in bytes, returns int."""
    return self.size - self.get_rescued_size()

  def get_percent_recovered(self):
    """Get percent rescued from map_data, returns float."""
    return 100 * self.map_data.get('rescued', 0) / self.size

  def get_rescued_size(self):
    """Get rescued size using map data.

    NOTE: Returns 0 if no map data is available.
    """
    self.load_map_data()
    return self.map_data.get('rescued', 0)

  def load_map_data(self):
    """Load map data from file.

    NOTE: If the file is missing it is assumed that recovery hasn't
          started yet so default values will be returned instead.
    """
    data = {'full recovery': False, 'pass completed': False}

    # Get output from ddrescuelog
    cmd = [
      'ddrescuelog',
      '--binary-prefixes',
      '--show-status',
      self.map_path,
      ]
    proc = exe.run_program(cmd, check=False)

    # Parse output
    for line in proc.stdout.splitlines():
      _r = DDRESCUE_LOG_REGEX.search(line)
      if _r:
        if _r.group('key') == 'rescued' and _r.group('percent') == '100':
          # Fix rounding errors from ddrescuelog output
          data['rescued'] = self.size
        else:
          data[_r.group('key')] = std.string_to_bytes(
            f'{_r.group("size")} {_r.group("unit")}',
            )
      data['pass completed'] = 'current status: finished' in line.lower()

    # Check if 100% done (only if map is present and non-zero size
    # NOTE: ddrescuelog returns 0 (i.e. 100% done) for empty files
    if self.map_path.exists() and self.map_path.stat().st_size != 0:
      cmd = [
        'ddrescuelog',
        '--done-status',
        self.map_path,
        ]
      proc = exe.run_program(cmd, check=False)
      data['full recovery'] = proc.returncode == 0

    # Done
    self.map_data.update(data)

  def pass_complete(self, pass_name):
    """Check if pass_num is complete based on map data, returns bool."""
    complete = False
    pending_size = 0

    # Check map data
    if self.map_data.get('full recovery', False):
      complete = True
    elif 'non-tried' not in self.map_data:
      # Assuming recovery has not been attempted yet
      complete = False
    else:
      # Check that current and previous passes are complete
      pending_size = self.map_data['non-tried']
      if pass_name in ('trim', 'scrape'):
        pending_size += self.map_data['non-trimmed']
      if pass_name == 'scrape':
        pending_size += self.map_data['non-scraped']
      if pending_size == 0:
        complete = True

    # Done
    return complete

  def safety_check(self):
    """Run safety check and abort if necessary."""
    dest_size = -1
    if self.destination.exists():
      dest_obj = hw_obj.Disk(self.destination)
      dest_size = dest_obj.details['size']
      del dest_obj

    # Check destination size if cloning
    if not self.destination.is_file() and dest_size < self.size:
      std.print_error(f'Invalid destination: {self.destination}')
      raise std.GenericAbort()

  def set_initial_status(self):
    """Read map data and set initial statuses."""
    self.load_map_data()
    percent = self.get_percent_recovered()
    for name in self.status.keys():
      if self.pass_complete(name):
        self.status[name] = percent
      else:
        # Stop checking
        if percent > 0:
          self.status[name] = percent
        break

  def skip_pass(self, pass_name):
    """Mark pass as skipped if applicable."""
    if self.status[pass_name] == 'Pending':
      self.status[pass_name] = 'Skipped'

  def update_progress(self, pass_name):
    """Update progress via map data."""
    self.load_map_data()

    # Update status
    percent = self.get_percent_recovered()
    if percent > 0:
      self.status[pass_name] = percent

    # Mark future passes as skipped if applicable
    if percent == 100:
      if pass_name == 'read':
        self.status['trim'] = 'Skipped'
      if pass_name in ('read', 'trim'):
        self.status['scrape'] = 'Skipped'


class State():
  """Object for tracking hardware diagnostic data."""
  def __init__(self):
    self.block_pairs = []
    self.destination = None
    self.log_dir = None
    self.mode = None
    self.panes = {}
    self.source = None
    self.working_dir = None

    # Start a background process to maintain layout
    self._init_tmux()
    exe.start_thread(self._fix_tmux_layout_loop)

  def _add_block_pair(self, source, destination):
    """Add BlockPair object and run safety checks."""
    self.block_pairs.append(
      BlockPair(
        source=source,
        destination=destination,
        model=self.source.details['model'],
        working_dir=self.working_dir,
        ))

  def _get_clone_settings_path(self):
    """get Clone settings file path, returns pathlib.Path obj."""
    description = self.source.details['model']
    if not description:
      description = self.source.path.name
    return pathlib.Path(f'{self.working_dir}/Clone_{description}.json')

  def _fix_tmux_layout(self, forced=True):
    """Fix tmux layout based on cfg.ddrescue.TMUX_LAYOUT."""
    layout = cfg.ddrescue.TMUX_LAYOUT
    needs_fixed = tmux.layout_needs_fixed(self.panes, layout)

    # Main layout fix
    try:
      tmux.fix_layout(self.panes, layout, forced=forced)
    except RuntimeError:
      # Assuming self.panes changed while running
      pass

    # Source/Destination
    if forced or needs_fixed:
      self.update_top_panes()

    # Return if Progress pane not present
    if 'Progress' not in self.panes:
      return

    # SMART/Journal
    if forced or needs_fixed:
      height = tmux.get_pane_size(self.panes['Progress'])[1] - 2
      p_ratios = [int((x/sum(PANE_RATIOS)) * height) for x in PANE_RATIOS]
      if 'SMART' in self.panes:
        tmux.resize_pane(self.panes['SMART'], height=p_ratios[0])
        tmux.resize_pane(height=p_ratios[1])
      if 'Journal' in self.panes:
        tmux.resize_pane(self.panes['Journal'], height=p_ratios[2])

  def _fix_tmux_layout_loop(self):
    """Fix tmux layout on a loop.

    NOTE: This should be called as a thread.
    """
    while True:
      self._fix_tmux_layout(forced=False)
      std.sleep(1)

  def _init_tmux(self):
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

  def _load_settings(self, discard_unused_settings=False):
    """Load settings from previous run, returns dict."""
    settings = {}
    settings_file = self._get_clone_settings_path()

    # Try loading JSON data
    if settings_file.exists():
      with open(settings_file, 'r') as _f:
        try:
          settings = json.loads(_f.read())
        except (OSError, json.JSONDecodeError):
          LOG.error('Failed to load clone settings')
          std.print_error('Invalid clone settings detected.')
          raise std.GenericAbort()

    # Check settings
    if settings:
      if settings['First Run'] and discard_unused_settings:
        # Previous run aborted before starting recovery, discard settings
        settings = {}
      else:
        bail = False
        for key in ('model', 'serial'):
          if settings['Source'][key] != self.source.details[key]:
            std.print_error(f"Clone settings don't match source {key}")
            bail = True
          if settings['Destination'][key] != self.destination.details[key]:
            std.print_error(f"Clone settings don't match destination {key}")
            bail = True
        if bail:
          raise std.GenericAbort()

    # Update settings
    if not settings:
      settings = CLONE_SETTINGS.copy()
    if not settings['Source']:
      settings['Source'] = {
        'model': self.source.details['model'],
        'serial': self.source.details['serial'],
        }
    if not settings['Destination']:
      settings['Destination'] = {
        'model': self.destination.details['model'],
        'serial': self.destination.details['serial'],
        }

    # Done
    return settings

  def _save_settings(self, settings):
    """Save settings for future runs."""
    settings_file = self._get_clone_settings_path()

    # Try saving JSON data
    try:
      with open(settings_file, 'w') as _f:
        json.dump(settings, _f)
    except OSError:
      std.print_error('Failed to save clone settings')
      raise std.GenericAbort()

  def add_clone_block_pairs(self):
    """Add device to device block pairs and set settings if necessary."""
    source_sep = get_partition_separator(self.source.path.name)
    dest_sep = get_partition_separator(self.destination.path.name)
    settings = {}
    source_parts = []

    # Clone settings
    settings = self._load_settings(discard_unused_settings=True)

    # Add pairs
    if settings['Partition Mapping']:
      # Resume previous run, load pairs from settings file
      for part_map in settings['Partition Mapping']:
        bp_source = hw_obj.Disk(
          f'{self.source.path}{source_sep}{part_map[0]}',
          )
        bp_dest = pathlib.Path(
          f'{self.destination.path}{dest_sep}{part_map[1]}',
          )
        self._add_block_pair(bp_source, bp_dest)
    else:
      source_parts = select_disk_parts('Clone', self.source)
      if self.source.path.samefile(source_parts[0].path):
        # Whole disk (or single partition via args), skip settings
        bp_dest = self.destination.path
        self._add_block_pair(self.source, bp_dest)
      else:
        # New run, use new settings file
        settings['Needs Format'] = True
        offset = 0
        user_choice = std.choice(
          ['G', 'M', 'S'],
          'Format clone using GPT, MBR, or match Source type?',
          )
        if user_choice == 'G':
          settings['Table Type'] = 'GPT'
        elif user_choice == 'M':
          settings['Table Type'] = 'MBR'
        else:
          # Match source type
          settings['Table Type'] = get_table_type(self.source)
        if std.ask('Create an empty Windows boot partition on the clone?'):
          settings['Create Boot Partition'] = True
          offset = 2 if settings['Table Type'] == 'GPT' else 1

        # Add pairs
        for dest_num, part in enumerate(source_parts):
          dest_num += offset + 1
          bp_dest = pathlib.Path(
            f'{self.destination.path}{dest_sep}{dest_num}',
            )
          self._add_block_pair(part, bp_dest)

          # Add to settings file
          source_num = re.sub(r'^.*?(\d+)$', r'\1', part.path.name)
          settings['Partition Mapping'].append([source_num, dest_num])

        # Save settings
        self._save_settings(settings)

    # Done
    return source_parts

  def add_image_block_pairs(self, source_parts):
    """Add device to image file block pairs."""
    for part in source_parts:
      bp_dest = self.destination
      self._add_block_pair(part, bp_dest)

  def confirm_selections(self, prompt, source_parts=None):
    """Show selection details and prompt for confirmation."""
    report = []

    # Source
    report.append(std.color_string('Source', 'GREEN'))
    report.extend(build_object_report(self.source))
    report.append(' ')

    # Destination
    report.append(std.color_string('Destination', 'GREEN'))
    if self.mode == 'Clone':
      report[-1] += std.color_string(' (ALL DATA WILL BE DELETED)', 'RED')
    report.extend(build_object_report(self.destination))
    report.append(' ')

    # Show deletion warning if necessary
    # NOTE: The check for block_pairs is to limit this section
    #       to the second confirmation
    if self.mode == 'Clone' and self.block_pairs:
      report.append(std.color_string('WARNING', 'YELLOW'))
      report.append(
        'All data will be deleted from the destination listed above.',
        )
      report.append(
        std.color_string(
          ['This is irreversible and will lead to', 'DATA LOSS.'],
          ['YELLOW', 'RED'],
          ),
        )
      report.append(' ')

    # Block pairs
    if self.block_pairs:
      report.extend(
        build_block_pair_report(
          self.block_pairs,
          self._load_settings() if self.mode == 'Clone' else {},
          ),
        )
      report.append(' ')

    # Map dir
    if self.working_dir:
      report.append(std.color_string('Map Save Directory', 'GREEN'))
      report.append(f'{self.working_dir}/')
      report.append(' ')
      if not fstype_is_ok(self.working_dir, map_dir=True):
        report.append(
          std.color_string(
            'Map file(s) are being saved to a non-recommended filesystem.',
            'YELLOW',
            ),
          )
        report.append(
          std.color_string(
            ['This is strongly discouraged and may lead to', 'DATA LOSS'],
            [None, 'RED'],
            ),
          )
        report.append(' ')

    # Source part(s) selected
    if source_parts:
      report.append(std.color_string('Source Part(s) selected', 'GREEN'))
      if self.source.path.samefile(source_parts[0].path):
        report.append('Whole Disk')
      else:
        report.append(std.color_string(f'{"NAME":<9} SIZE', 'BLUE'))
        for part in source_parts:
          report.append(
            f'{part.path.name:<9} '
            f'{std.bytes_to_string(part.details["size"], use_binary=False)}'
            )
      report.append(' ')

    # Prompt user
    std.clear_screen()
    std.print_report(report)
    if not std.ask(prompt):
      raise std.GenericAbort()

  def generate_report(self):
    """Generate report of overall and per block_pair results, returns list."""
    report = []

    # Header
    report.append(f'{self.mode.title()} Results:')
    report.append(' ')
    report.append(f'Source: {self.source.description}')
    if self.mode == 'Clone':
      report.append(f'Destination: {self.destination.description}')
    else:
      report.append(f'Destination: {self.destination}/')

    # Overall
    report.append(' ')
    error_size = self.get_error_size()
    error_size_str = std.bytes_to_string(error_size, decimals=2)
    if error_size > 0:
      error_size_str = std.color_string(error_size_str, 'YELLOW')
    percent = self.get_percent_recovered()
    percent = format_status_string(percent, width=0)
    report.append(f'Overall rescued: {percent}, error size: {error_size_str}')

    # Block-Pairs
    if len(self.block_pairs) > 1:
      report.append(' ')
      for pair in self.block_pairs:
        error_size = pair.get_error_size()
        error_size_str = std.bytes_to_string(error_size, decimals=2)
        if error_size > 0:
          error_size_str = std.color_string(error_size_str, 'YELLOW')
        pair_size = std.bytes_to_string(pair.size, decimals=2)
        percent = pair.get_percent_recovered()
        percent = format_status_string(percent, width=0)
        report.append(
          f'{pair.source.name} ({pair_size}) '
          f'rescued: {percent}, '
          f'error size: {error_size_str}'
          )

    # Done
    return report

  def get_error_size(self):
    """Get total error size from block_pairs in bytes, returns int."""
    return self.get_total_size() - self.get_rescued_size()

  def get_percent_recovered(self):
    """Get total percent rescued from block_pairs, returns float."""
    return 100 * self.get_rescued_size() / self.get_total_size()

  def get_rescued_size(self):
    """Get total rescued size from all block pairs, returns int."""
    return sum([pair.get_rescued_size() for pair in self.block_pairs])

  def get_total_size(self):
    """Get total size of all block_pairs in bytes, returns int."""
    return sum([pair.size for pair in self.block_pairs])

  def init_recovery(self, docopt_args):
    """Select source/dest and set env."""
    std.clear_screen()
    source_parts = []

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
    self.mode = set_mode(docopt_args)

    # Select source
    self.source = get_object(docopt_args['<source>'])
    if not self.source:
      self.source = select_disk('Source')
    self.update_top_panes()

    # Select destination
    self.destination = get_object(docopt_args['<destination>'])
    if not self.destination:
      if self.mode == 'Clone':
        self.destination = select_disk('Destination', self.source)
      elif self.mode == 'Image':
        self.destination = select_path('Destination')
    self.update_top_panes()

    # Confirmation #1
    self.confirm_selections(
      prompt='Are these selections correct?',
      source_parts=source_parts,
      )

    # Update panes
    self.panes['Progress'] = tmux.split_window(
      lines=cfg.ddrescue.TMUX_SIDE_WIDTH,
      watch_file=f'{self.log_dir}/progress.out',
      )
    self.update_progress_pane('Idle')

    # Set working dir
    self.working_dir = get_working_dir(
      self.mode,
      self.destination,
      force_local=docopt_args['--force-local-map'],
      )

    # Start fresh if requested
    if docopt_args['--start-fresh']:
      clean_working_dir(self.working_dir)

    # Add block pairs
    if self.mode == 'Clone':
      source_parts = self.add_clone_block_pairs()
    else:
      source_parts = select_disk_parts(self.mode, self.source)
      self.add_image_block_pairs(source_parts)

    # Safety Checks #1
    if self.mode == 'Clone':
      self.safety_check_destination()
    self.safety_check_size()

    # Confirmation #2
    self.update_progress_pane('Idle')
    self.confirm_selections('Start recovery?')

    # Prep destination
    if self.mode == 'Clone':
      self.prep_destination(source_parts, dry_run=docopt_args['--dry-run'])

    # Safety Checks #2
    if not docopt_args['--dry-run']:
      for pair in self.block_pairs:
        pair.safety_check()

  def mark_started(self):
    """Edit clone settings, if applicable, to mark recovery as started."""
    # Skip if not cloning
    if self.mode != 'Clone':
      return

    # Skip if not using settings
    # i.e. Cloning whole disk (or single partition via args)
    if self.source.path.samefile(self.block_pairs[0].source):
      return

    # Update settings
    settings = self._load_settings()
    if settings.get('First Run', False):
      settings['First Run'] = False
      self._save_settings(settings)

  def pass_above_threshold(self, pass_name):
    """Check if all block_pairs meet the pass threshold, returns bool."""
    threshold = cfg.ddrescue.AUTO_PASS_THRESHOLDS[pass_name]
    return all(
      [p.get_percent_recovered() >= threshold for p in self.block_pairs],
      )

  def pass_complete(self, pass_name):
    """Check if all block_pairs completed pass_name, returns bool."""
    return all([p.pass_complete(pass_name) for p in self.block_pairs])

  def prep_destination(self, source_parts, dry_run=True):
    """Prep destination as necessary."""
    # TODO: Split into Linux and macOS
    #       logical sector size is not easily found under macOS
    #       It might be easier to rewrite this section using macOS tools
    dest_prefix = str(self.destination.path)
    dest_prefix += get_partition_separator(self.destination.path.name)
    esp_type = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
    msr_type = 'E3C9E316-0B5C-4DB8-817D-F92DF00215AE'
    part_num = 0
    sfdisk_script = []
    settings = self._load_settings()

    # Bail early
    if not settings['Needs Format']:
      return

    # Add partition table settings
    if settings['Table Type'] == 'GPT':
      sfdisk_script.append('label: gpt')
    else:
      sfdisk_script.append('label: dos')
    sfdisk_script.append('unit: sectors')
    sfdisk_script.append('')

    # Add boot partition if requested
    if settings['Create Boot Partition']:
      if settings['Table Type'] == 'GPT':
        part_num += 1
        sfdisk_script.append(
          build_sfdisk_partition_line(
            table_type='GPT',
            dev_path=f'{dest_prefix}{part_num}',
            size='384MiB',
            details={'parttype': esp_type, 'partlabel': 'EFI System'},
            ),
          )
        part_num += 1
        sfdisk_script.append(
          build_sfdisk_partition_line(
            table_type=settings['Table Type'],
            dev_path=f'{dest_prefix}{part_num}',
            size='16MiB',
            details={'parttype': msr_type, 'partlabel': 'Microsoft Reserved'},
            ),
          )
      elif settings['Table Type'] == 'MBR':
        part_num += 1
        sfdisk_script.append(
          build_sfdisk_partition_line(
            table_type='MBR',
            dev_path=f'{dest_prefix}{part_num}',
            size='100MiB',
            details={'parttype': '0x7', 'partlabel': 'System Reserved'},
            ),
          )

    # Add selected partition(s)
    for part in source_parts:
      num_sectors = part.details['size'] / self.destination.details['log-sec']
      num_sectors = math.ceil(num_sectors)
      part_num += 1
      sfdisk_script.append(
        build_sfdisk_partition_line(
          table_type=settings['Table Type'],
          dev_path=f'{dest_prefix}{part_num}',
          size=num_sectors,
          details=part.details,
          ),
        )

    # Save sfdisk script
    script_path = (
      f'{self.working_dir}/'
      f'sfdisk_{self.destination.path.name}.script'
      )
    with open(script_path, 'w') as _f:
      _f.write('\n'.join(sfdisk_script))

    # Skip real format for dry runs
    if dry_run:
      LOG.info('Dry run, refusing to format destination')
      return

    # Format disk
    LOG.warning('Formatting destination: %s', self.destination.path)
    with open(script_path, 'r') as _f:
      proc = exe.run_program(
        cmd=['sudo', 'sfdisk', self.destination.path],
        stdin=_f,
        check=False,
        )
      if proc.returncode != 0:
        std.print_error('Error(s) encoundtered while formatting destination')
        raise std.GenericAbort()

    # Update settings
    settings['Needs Format'] = False
    self._save_settings(settings)

  def retry_all_passes(self):
    """Prep block_pairs for a retry recovery attempt."""
    bad_statuses = ('*', '/', '-')
    LOG.warning('Updating block_pairs for retry')

    # Update all block_pairs
    for pair in self.block_pairs:
      map_data = []

      # Reset status strings
      for name in pair.status.keys():
        pair.status[name] = 'Pending'

      # Mark all non-trimmed, non-scraped, and bad areas as non-tried
      with open(pair.map_path, 'r') as _f:
        for line in _f.readlines():
          line = line.strip()
          if line.startswith('0x') and line.endswith(bad_statuses):
            line = f'{line[:-1]}?'
          map_data.append(line)

      # Save updated map
      with open(pair.map_path, 'w') as _f:
        _f.write('\n'.join(map_data))

      # Reinitialize status
      pair.set_initial_status()

  def safety_check_destination(self):
    """Run safety checks for destination and abort if necessary."""
    try:
      self.destination.safety_checks()
    except hw_obj.CriticalHardwareError:
      std.print_error(
        f'Critical error(s) detected for: {self.destination.path}',
        )
      raise std.GenericAbort()

  def safety_check_size(self):
    """Run size safety check and abort if necessary."""
    required_size = sum([pair.size for pair in self.block_pairs])
    settings = self._load_settings() if self.mode == 'Clone' else {}

    # Increase required_size if necessary
    if self.mode == 'Clone' and settings.get('Needs Format', False):
      if settings['Table Type'] == 'GPT':
        # Below is the size calculation for the GPT
        #   1 LBA for the protective MBR
        #   33 LBAs each for the primary and backup GPT tables
        # Source: https://en.wikipedia.org/wiki/GUID_Partition_Table
        required_size += (1 + 33 + 33) * self.destination.details['phy-sec']
        if settings['Create Boot Partition']:
          # 384MiB EFI System Partition and a 16MiB MS Reserved partition
          required_size += (384 + 16) * 1024**2
      else:
        # MBR only requires one LBA but adding a full 4096 bytes anyway
        required_size += 4096
        if settings['Create Boot Partition']:
          # 100MiB System Reserved partition
          required_size += 100 * 1024**2

    # Reduce required_size if necessary
    if self.mode == 'Image':
      for pair in self.block_pairs:
        if pair.destination.exists():
          # NOTE: This uses the "max space" of the destination
          #       i.e. not the apparent size which is smaller for sparse files
          #       While this can result in an out-of-space error it's better
          #       than nothing.
          required_size -= pair.destination.stat().st_size

    # Check destination size
    if self.mode == 'Clone':
      destination_size = self.destination.details['size']
      error_msg = 'A larger destination disk is required'
    else:
      # NOTE: Adding an extra 5% here to better ensure it will fit
      destination_size = psutil.disk_usage(self.destination).free
      destination_size *= 1.05
      error_msg = 'Not enough free space on the destination'
    if required_size > destination_size:
      std.print_error(error_msg)
      raise std.GenericAbort()

  def save_debug_reports(self):
    """Save debug reports to disk."""
    LOG.info('Saving debug reports')
    debug_dir = pathlib.Path(f'{self.log_dir}/debug')
    if not debug_dir.exists():
      debug_dir.mkdir()

    # State (self)
    with open(f'{debug_dir}/state.report', 'a') as _f:
      _f.write('[Debug report]\n')
      _f.write('\n'.join(debug.generate_object_report(self)))
      _f.write('\n')

    # Block pairs
    for _bp in self.block_pairs:
      with open(f'{debug_dir}/block_pairs.report', 'a') as _f:
        _f.write('[Debug report]\n')
        _f.write('\n'.join(debug.generate_object_report(_bp)))
        _f.write('\n')

  def skip_pass(self, pass_name):
    """Mark block_pairs as skipped if applicable."""
    for pair in self.block_pairs:
      if pair.status[pass_name] == 'Pending':
        pair.status[pass_name] = 'Skipped'

  def update_progress_pane(self, overall_status):
    """Update progress pane."""
    report = []
    separator = '─────────────────────'
    width = cfg.ddrescue.TMUX_SIDE_WIDTH

    # Status
    report.append(std.color_string(f'{"Status":^{width}}', 'BLUE'))
    if 'NEEDS ATTENTION' in overall_status:
      report.append(
        std.color_string(f'{overall_status:^{width}}', 'YELLOW_BLINK'),
        )
    else:
      report.append(f'{overall_status:^{width}}')
    report.append(separator)

    # Overall progress
    if self.block_pairs:
      total_rescued = self.get_rescued_size()
      percent = self.get_percent_recovered()
      report.append(std.color_string('Overall Progress', 'BLUE'))
      report.append(
        f'Rescued: {format_status_string(percent, width=width-9)}',
        )
      report.append(
        std.color_string(
          [f'{std.bytes_to_string(total_rescued, decimals=2):>{width}}'],
          [get_percent_color(percent)],
          ),
        )
      report.append(separator)

    # Block pair progress
    for pair in self.block_pairs:
      report.append(std.color_string(pair.source, 'BLUE'))
      for name, status in pair.status.items():
        name = name.title()
        report.append(
          f'{name}{format_status_string(status, width=width-len(name))}',
          )
      report.append(' ')

    # EToC
    if overall_status in ('Active', 'NEEDS ATTENTION'):
      etoc = get_etoc()
      report.append(separator)
      report.append(std.color_string('Estimated Pass Finish', 'BLUE'))
      if overall_status == 'NEEDS ATTENTION' or etoc == 'N/A':
        report.append(std.color_string('N/A', 'YELLOW'))
      else:
        report.append(etoc)

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
def build_block_pair_report(block_pairs, settings):
  """Build block pair report, returns list."""
  report = []
  notes = []
  if block_pairs:
    report.append(std.color_string('Block Pairs', 'GREEN'))
  else:
    # Bail early
    return report

  # Show block pair mapping
  if settings and settings['Create Boot Partition']:
    if settings['Table Type'] == 'GPT':
      report.append(f'{" —— ":<9} --> EFI System Partition')
      report.append(f'{" —— ":<9} --> Microsoft Reserved Partition')
    elif settings['Table Type'] == 'MBR':
      report.append(f'{" —— ":<9} --> System Reserved')
  for pair in block_pairs:
    report.append(f'{pair.source.name:<9} --> {pair.destination.name}')

  # Show resume messages as necessary
  if settings:
    if not settings['First Run']:
      notes.append(
        std.color_string(
          ['NOTE:', 'Clone settings loaded from previous run.'],
          ['BLUE', None],
          ),
        )
    if settings['Needs Format'] and settings['Table Type']:
      msg = f'Destination will be formatted using {settings["Table Type"]}'
      notes.append(
        std.color_string(
          ['NOTE:', msg],
          ['BLUE', None],
          ),
        )
  if any([pair.get_rescued_size() > 0 for pair in block_pairs]):
    notes.append(
      std.color_string(
        ['NOTE:', 'Resume data loaded from map file(s).'],
        ['BLUE', None],
        ),
      )

  # Add notes to report
  if notes:
    report.append(' ')
    report.extend(notes)

  # Done
  return report


def build_ddrescue_cmd(block_pair, pass_name, settings):
  """Build ddrescue cmd using passed details, returns list."""
  cmd = ['sudo', 'ddrescue']
  if (block_pair.destination.is_block_device()
      or block_pair.destination.is_char_device()):
    cmd.append('--force')
  if pass_name == 'read':
    cmd.extend(['--no-trim', '--no-scrape'])
  elif pass_name == 'trim':
    # Allow trimming
    cmd.append('--no-scrape')
  elif pass_name == 'scrape':
    # Allow trimming and scraping
    pass
  cmd.extend(settings)
  cmd.append(block_pair.source)
  cmd.append(block_pair.destination)
  cmd.append(block_pair.map_path)

  # Done
  LOG.debug('ddrescue cmd: %s', cmd)
  return cmd


def build_directory_report(path):
  """Build directory report, returns list."""
  path = f'{path}/'
  report = []

  # Get details
  if PLATFORM == 'Linux':
    cmd = [
      'findmnt',
      '--output', 'SIZE,AVAIL,USED,FSTYPE,OPTIONS',
      '--target', path,
      ]
    proc = exe.run_program(cmd)
    width = len(path) + 1
    for line in proc.stdout.splitlines():
      line = line.replace('\n', '')
      if 'FSTYPE' in line:
        line = std.color_string(f'{"PATH":<{width}}{line}', 'BLUE')
      else:
        line = f'{path:<{width}}{line}'
      report.append(line)
  else:
    # TODO Get dir details under macOS
    report.append(std.color_string('PATH', 'BLUE'))
    report.append(str(path))

  # Done
  return report


def build_disk_report(dev):
  """Build device report, returns list."""
  children = dev.details.get('children', [])
  report = []

  # Get widths
  widths = {
    'fstype': max(6, len(str(dev.details.get('fstype', '')))),
    'label': max(5, len(str(dev.details.get('label', '')))),
    'name': max(4, len(dev.path.name)),
    }
  for child in children:
    widths['fstype'] = max(widths['fstype'], len(str(child['fstype'])))
    widths['label'] = max(widths['label'], len(str(child['label'])))
    widths['name'] = max(
      widths['name'],
      len(child['name'].replace('/dev/', '')),
      )
  widths = {k: v+1 for k, v in widths.items()}

  # Disk details
  report.append(f'{dev.path.name} {dev.description}')
  report.append(' ')
  dev_fstype = dev.details.get('fstype', '')
  dev_label = dev.details.get('label', '')
  dev_name = dev.path.name
  dev_size = std.bytes_to_string(dev.details["size"], use_binary=False)

  # Partition details
  report.append(
    std.color_string(
      (
        f'{"NAME":<{widths["name"]}}'
        f'{"  " if children else ""}'
        f'{"SIZE":<7}'
        f'{"FSTYPE":<{widths["fstype"]}}'
        f'{"LABEL":<{widths["label"]}}'
      ),
      'BLUE',
      ),
    )
  report.append(
    f'{dev_name if dev_name else "":<{widths["name"]}}'
    f'{"  " if children else ""}'
    f'{dev_size:>6} '
    f'{dev_fstype if dev_fstype else "":<{widths["fstype"]}}'
    f'{dev_label if dev_label else "":<{widths["label"]}}'
  )
  for child in children:
    fstype = child['fstype']
    label = child['label']
    name = child['name'].replace('/dev/', '')
    size = std.bytes_to_string(child["size"], use_binary=False)
    report.append(
      f'{name if name else "":<{widths["name"]}}'
      f'{size:>6} '
      f'{fstype if fstype else "":<{widths["fstype"]}}'
      f'{label if label else "":<{widths["label"]}}'
    )

  # Indent children
  if len(children) > 1:
    report = [
      *report[:4],
      *[f'├─{line}' for line in report[4:-1]],
      f'└─{report[-1]}',
      ]
  elif len(children) == 1:
    report[-1] = f'└─{report[-1]}'

  # Done
  return report


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


def build_object_report(obj):
  """Build object report, returns list."""
  report = []

  # Get details based on object given
  if hasattr(obj, 'is_dir') and obj.is_dir():
    # Directory report
    report = build_directory_report(obj)
  else:
    # Device report
    report = build_disk_report(obj)

  # Done
  return report


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
  menu.add_action('Load Preset')
  menu.add_action('Main Menu')
  for name, details in cfg.ddrescue.DDRESCUE_SETTINGS['Default'].items():
    menu.add_option(name, details.copy())

  # Update settings using preset
  if preset != 'Default':
    for name, details in cfg.ddrescue.DDRESCUE_SETTINGS[preset].items():
      menu.options[name].update(details.copy())

  # Done
  return menu


def build_sfdisk_partition_line(table_type, dev_path, size, details):
  """Build sfdisk partition line using passed details, returns str."""
  line = f'{dev_path} : size={size}'
  dest_type = ''
  source_filesystem = str(details.get('fstype', '')).upper()
  source_table_type = ''
  source_type = details.get('parttype', '')

  # Set dest type
  if re.match(r'^0x\w+$', source_type):
    # Both source and dest are MBR
    source_table_type = 'MBR'
    if table_type == 'MBR':
      dest_type = source_type.replace('0x', '').lower()
  elif re.match(r'^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', source_type):
    # Source is a GPT type
    source_table_type = 'GPT'
    if table_type == 'GPT':
      dest_type = source_type.upper()
  if not dest_type:
    # Assuming changing table types, set based on FS
    if source_filesystem in cfg.ddrescue.PARTITION_TYPES.get(table_type, {}):
      dest_type = cfg.ddrescue.PARTITION_TYPES[table_type][source_filesystem]
  line += f', type={dest_type}'

  # Safety Check
  if not dest_type:
    std.print_error(f'Failed to determine partition type for: {dev_path}')
    raise std.GenericAbort()

  # Add extra details
  if details.get('partlabel', ''):
    line += f', name="{details["partlabel"]}"'
  if details.get('partuuid', '') and source_table_type == table_type:
    # Only add UUID if source/dest table types match
    line += f', uuid={details["partuuid"].upper()}'

  # Done
  return line


def clean_working_dir(working_dir):
  """Clean working directory to ensure a fresh recovery session.

  NOTE: Data from previous sessions will be preserved
        in a backup directory.
  """
  backup_dir = pathlib.Path(f'{working_dir}/prev')
  backup_dir = io.non_clobber_path(backup_dir)
  backup_dir.mkdir()

  # Move settings, maps, etc to backup_dir
  for entry in os.scandir(working_dir):
    if entry.name.endswith(('.dd', '.json', '.map')):
      new_path = f'{backup_dir}/{entry.name}'
      new_path = io.non_clobber_path(new_path)
      shutil.move(entry.path, new_path)


def format_status_string(status, width):
  """Format colored status string, returns str."""
  color = None
  percent = -1
  status_str = str(status)

  # Check if status is percentage
  try:
    percent = float(status_str)
  except ValueError:
    # Assuming status is text
    pass

  # Format status
  if percent >= 0:
    # Percentage
    color = get_percent_color(percent)
    status_str = f'{percent:{width-2}.2f} %'
    if '100.00' in status_str and percent < 100:
      # Always round down to 99.99%
      LOG.warning('Rounding down to 99.99 from %s', percent)
      status_str = f'{"99.99 %":>{width}}'
  else:
    # Text
    color = STATUS_COLORS.get(status_str, None)
    status_str = f'{status_str:>{width}}'

  # Add color if necessary
  if color:
    status_str = std.color_string(status_str, color)

  # Done
  return status_str


def fstype_is_ok(path, map_dir=False):
  """Check if filesystem type is acceptable, returns bool."""
  is_ok = False
  fstype = None

  # Get fstype
  if PLATFORM == 'Darwin':
    # TODO: Determine fstype under macOS
    pass
  elif PLATFORM == 'Linux':
    cmd = [
      'findmnt',
      '--noheadings',
      '--output', 'FSTYPE',
      '--target', path,
      ]
    proc = exe.run_program(cmd, check=False)
    fstype = proc.stdout
  fstype = fstype.strip().lower()

  # Check fstype
  if map_dir:
    is_ok = RECOMMENDED_MAP_FSTYPES.match(fstype)
  else:
    is_ok = RECOMMENDED_FSTYPES.match(fstype)

  # Done
  return is_ok


def get_ddrescue_settings(settings_menu):
  """Get ddrescue settings from menu selections, returns list."""
  settings = []

  # Check menu selections
  for name, details in settings_menu.options.items():
    if details['Selected']:
      if 'Value' in details:
        settings.append(f'{name}={details["Value"]}')
      else:
        settings.append(name)

  # Done
  return settings


def get_etoc():
  """Get EToC from ddrescue output, returns str."""
  delta = None
  delta_dict = {}
  etoc = 'Unknown'
  now = datetime.datetime.now(tz=TIMEZONE)
  output = tmux.capture_pane()

  # Search for EToC delta
  matches = re.findall(f'remaining time:.*$', output, re.MULTILINE)
  if matches:
    match = REGEX_REMAINING_TIME.search(matches[-1])
    if match.group('na'):
      etoc = 'N/A'
    else:
      for key in ('days', 'hours', 'minutes', 'seconds'):
        delta_dict[key] = match.group(key)
      delta_dict = {k: int(v) if v else 0 for k, v in delta_dict.items()}
      delta = datetime.timedelta(**delta_dict)

  # Calc EToC if delta found
  if delta:
    etoc_datetime = now + delta
    etoc = etoc_datetime.strftime('%Y-%m-%d %H:%M %Z')

  # Done
  return etoc


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


def get_partition_separator(name):
  """Get partition separator based on device name, returns str."""
  separator = ''
  if re.search(r'(loop|mmc|nvme)', name, re.IGNORECASE):
    separator = 'p'

  return separator


def get_percent_color(percent):
  """Get color based on percentage, returns str."""
  color = None
  if percent > 100:
    color = 'PURPLE'
  elif percent >= 99:
    color = 'GREEN'
  elif percent >= 90:
    color = 'YELLOW'
  elif percent > 0:
    color = 'RED'

  # Done
  return color


def get_table_type(disk):
  """Get disk partition table type, returns str.

  NOTE: If resulting table type is not GPT or MBR
        then an exception is raised.
  """
  table_type = str(disk.details.get('pttype', '')).upper()
  table_type = table_type.replace('DOS', 'MBR')

  # Check type
  if table_type not in ('GPT', 'MBR'):
    std.print_error(f'Unsupported partition table type: {table_type}')
    raise std.GenericAbort()

  # Done
  return table_type


def get_working_dir(mode, destination, force_local=False):
  """Get working directory using mode and destination, returns path."""
  ticket_id = None
  working_dir = None

  # Set ticket ID
  while ticket_id is None:
    ticket_id = std.input_text(
      prompt='Please enter ticket ID:',
      allow_empty_response=False,
      )
    ticket_id = ticket_id.replace(' ', '_')
    if not re.match(r'^\d+', ticket_id):
      ticket_id = None

  # Use preferred path if possible
  if mode == 'Image':
    try:
      path = pathlib.Path(destination).resolve()
    except TypeError:
      std.print_error(f'Invalid destination: {destination}')
      raise std.GenericAbort()
    if path.exists() and fstype_is_ok(path, map_dir=False):
      working_dir = path
  elif mode == 'Clone' and not force_local:
    std.print_info('Mounting backup shares...')
    net.mount_backup_shares(read_write=True)
    for server in cfg.net.BACKUP_SERVERS:
      path = pathlib.Path(f'/Backups/{server}')
      if path.exists() and fstype_is_ok(path, map_dir=True):
        # Acceptable path found
        working_dir = path
        break

  # Default to current dir if necessary
  if not working_dir:
    LOG.error('Failed to set preferred working directory')
    working_dir = pathlib.Path(os.getcwd())

  # Set subdir using ticket ID
  if mode == 'Clone':
    working_dir = working_dir.joinpath(ticket_id)

  # Create directory
  working_dir.mkdir(parents=True, exist_ok=True)
  os.chdir(working_dir)

  # Done
  LOG.info('Set working directory to: %s', working_dir)
  return working_dir


def main():
  """Main function for ddrescue TUI."""
  args = docopt(DOCSTRING)
  log.update_log_path(dest_name='ddrescue-TUI', timestamp=True)

  # Check if running inside tmux
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
      std.clear_screen()
      run_recovery(state, main_menu, settings_menu, dry_run=args['--dry-run'])

    # Quit
    if 'Quit' in selection:
      total_percent = state.get_percent_recovered()
      if total_percent == 100:
        break

      # Recovey < 100%
      std.print_warning('Recovery is less than 100%')
      if std.ask('Are you sure you want to quit?'):
        break

  # Save results to log
  LOG.info('')
  for line in state.generate_report():
    LOG.info('  %s', std.strip_colors(line))


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


def run_ddrescue(state, block_pair, pass_name, settings, dry_run=True):
  """Run ddrescue using passed settings."""
  cmd = build_ddrescue_cmd(block_pair, pass_name, settings)
  state.update_progress_pane('Active')
  std.clear_screen()
  warning_message = ''

  def _update_smart_pane():
    """Update SMART pane every 30 seconds."""
    state.source.update_smart_details()
    now = datetime.datetime.now(tz=TIMEZONE).strftime('%Y-%m-%d %H:%M %Z')
    with open(f'{state.log_dir}/smart.out', 'w') as _f:
      _f.write(
        std.color_string(
          ['SMART Attributes', f'Updated: {now}\n'],
          ['BLUE', 'YELLOW'],
          sep='\t\t',
          ),
        )
      _f.write('\n'.join(state.source.generate_report(header=False)))

  # Dry run
  if dry_run:
    LOG.info('ddrescue cmd: %s', cmd)
    return

  # Start ddrescue
  proc = exe.popen_program(cmd)

  # ddrescue loop
  _i = 0
  while True:
    if _i % 30 == 0:
      # Update SMART pane
      _update_smart_pane()
    if _i % 60 == 0:
      # Clear ddrescue pane
      tmux.clear_pane()
    _i += 1

    # Update progress
    block_pair.update_progress(pass_name)
    state.update_progress_pane('Active')

    # Check if complete
    try:
      proc.wait(timeout=1)
      break
    except KeyboardInterrupt:
      # Wait a bit to let ddrescue exit safely
      LOG.warning('ddrescue stopped by user')
      warning_message = 'Aborted'
      std.sleep(2)
      exe.run_program(['sudo', 'kill', str(proc.pid)], check=False)
      break
    except subprocess.TimeoutExpired:
      # Continue to next loop to update panes
      pass
    else:
      # Done
      std.sleep(1)
      break

  # Update progress
  # NOTE: Using 'Active' here to avoid flickering between block pairs
  block_pair.update_progress(pass_name)
  state.update_progress_pane('Active')

  # Check result
  if proc.poll():
    # True if return code is non-zero (poll() returns None if still running)
    warning_message = 'Error(s) encountered, see message above'
  if warning_message:
    print(' ')
    print(' ')
    std.print_error('DDRESCUE PROCESS HALTED')
    print(' ')
    std.print_warning(warning_message)

  # Needs attention?
  if str(proc.poll()) != '0':
    state.update_progress_pane('NEEDS ATTENTION')
    std.pause('Press Enter to return to main menu...')
    raise std.GenericAbort()


def run_recovery(state, main_menu, settings_menu, dry_run=True):
  """Run recovery passes."""
  atexit.register(state.save_debug_reports)
  attempted_recovery = False
  auto_continue = False

  # Get settings
  for name, details in main_menu.toggles.items():
    if 'Auto continue' in name and details['Selected']:
      auto_continue = True
    if 'Retry' in name and details['Selected']:
      details['Selected'] = False
      state.retry_all_passes()
  settings = get_ddrescue_settings(settings_menu)

  # Start SMART/Journal
  state.panes['SMART'] = tmux.split_window(
    behind=True, lines=12, vertical=True,
    watch_file=f'{state.log_dir}/smart.out',
    )
  state.panes['Journal'] = tmux.split_window(
    lines=4, vertical=True, cmd='journalctl --dmesg --follow',
    )

  # Run pass(es)
  for pass_name in ('read', 'trim', 'scrape'):
    abort = False

    # Skip to next pass
    if state.pass_complete(pass_name):
      # NOTE: This bypasses auto_continue
      state.skip_pass(pass_name)
      continue

    # Run ddrescue
    for pair in state.block_pairs:
      if not pair.pass_complete(pass_name):
        attempted_recovery = True
        state.mark_started()
        try:
          run_ddrescue(state, pair, pass_name, settings, dry_run=dry_run)
        except (KeyboardInterrupt, std.GenericAbort):
          abort = True
          break

    # Continue or return to menu
    all_complete = state.pass_complete(pass_name)
    all_above_threshold = state.pass_above_threshold(pass_name)
    if abort or not (all_complete and all_above_threshold and auto_continue):
      LOG.warning('Recovery halted')
      break

  # Stop SMART/Journal
  for pane in ('SMART', 'Journal'):
    if pane in state.panes:
      tmux.kill_pane(state.panes.pop(pane))

  # Show warning if nothing was done
  if not attempted_recovery:
    std.print_warning('No actions performed')
    std.print_standard(' ')
    std.pause('Press Enter to return to main menu...')

  # Done
  state.save_debug_reports()
  atexit.unregister(state.save_debug_reports)
  state.update_progress_pane('Idle')


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

  def _select_parts(menu):
    """Loop over selection menu until at least one partition selected."""
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
  _select_parts(menu)

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
