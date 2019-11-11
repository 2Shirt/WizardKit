"""WizardKit: tmux Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import pathlib

from wk.exe import run_program


# STATIC_VARIABLES
LOG = logging.getLogger(__name__)


# Functions
def capture_pane(pane_id=None):
  """Capture text from current or target pane, returns str."""
  cmd = ['tmux', 'capture-pane', '-p']
  if pane_id:
    cmd.extend(['-t', pane_id])

  # Capture and return
  proc = run_program(cmd, check=False)
  return proc.stdout.strip()


def get_pane_size(pane_id=None):
  """Get current or target pane size, returns tuple."""
  cmd = ['tmux', 'display', '-p']
  if pane_id:
    cmd.extend(['-t', pane_id])
  cmd.append('#{pane_width} #{pane_height}')

  # Get resolution
  proc = run_program(cmd, check=False)
  width, height = proc.stdout.strip().split()
  width = int(width)
  height = int(height)

  # Done
  return (width, height)


def kill_all_panes(pane_id=None):
  """Kill all panes except for the current or target pane."""
  cmd = ['tmux', 'kill-pane', '-a']
  if pane_id:
    cmd.extend(['-t', pane_id])

  # Kill
  run_program(cmd, check=False)


def kill_pane(*pane_ids):
  """Kill pane(s) by id."""
  cmd = ['tmux', 'kill-pane', '-t']

  # Iterate over all passed pane IDs
  for pane_id in pane_ids:
    run_program(cmd+[pane_id], check=False)


def poll_pane(pane_id):
  """Check if pane exists, returns bool."""
  cmd = ['tmux', 'list-panes', '-F', '#D']

  # Get list of panes
  proc = run_program(cmd, check=False)
  existant_panes = proc.stdout.splitlines()

  # Check if pane exists
  return pane_id in existant_panes


def prep_action(
    cmd=None, working_dir=None, text=None, watch_file=None, watch_cmd='cat'):
  """Prep action to perform during a tmux call, returns list.

  This will prep for running a basic command, displaying text on screen,
  or monitoring a file. The last option uses cat by default but can be
  overridden by using the watch_cmd.
  """
  action_cmd = []
  if working_dir:
    action_cmd.extend(['-c', working_dir])

  if cmd:
    # Basic command
    action_cmd.append(cmd)
  elif text:
    # Display text
    action_cmd.extend([
      'watch',
      '--color',
      '--exec',
      '--no-title',
      '--interval', '1',
      'echo', '-e', text,
      ])
  elif watch_file:
    # Monitor file
    prep_file(watch_file)
    action_cmd.extend([
      'watch',
      '--color',
      '--no-title',
      '--interval', '1',
      ])
    if watch_cmd == 'cat':
      action_cmd.append('cat')
    elif watch_cmd == 'tail':
      action_cmd.extend(['tail', '--follow'])
    action_cmd.append(watch_file)
  else:
    LOG.error('No action specified')
    raise RuntimeError('No action specified')

  # Done
  return action_cmd


def prep_file(path):
  """Check if file exists and create empty file if not."""
  path = pathlib.Path(path).resolve()
  try:
    path.touch(exist_ok=False)
  except FileExistsError:
    # Leave existing files alone
    pass


def resize_pane(pane_id=None, width=None, height=None):
  """Resize current or target pane."""
  cmd = ['tmux', 'resize-pane']

  # Safety checks
  if not poll_pane(pane_id):
    LOG.error('tmux pane %s not found', pane_id)
    raise RuntimeError(f'tmux pane {pane_id} not found')
  if not (width or height):
    LOG.error('Neither width nor height specified')
    raise RuntimeError('Neither width nor height specified')

  # Finish building cmd
  if pane_id:
    cmd.extend(['-t', pane_id])
  if width:
    cmd.extend(['-x', str(width)])
  if height:
    cmd.extend(['-y', str(height)])

  # Resize
  run_program(cmd, check=False)


def split_window(
    lines=None, percent=None,
    behind=False, vertical=False,
    target_id=None, **action):
  """Split tmux window, run action, and return pane_id as str."""
  cmd = ['tmux', 'split-window', '-d', '-PF', '#D']

  # Safety checks
  if not (lines or percent):
    LOG.error('Neither lines nor percent specified')
    raise RuntimeError('Neither lines nor percent specified')

  # New pane placement
  if behind:
    cmd.append('-b')
  if vertical:
    cmd.append('-v')
  else:
    cmd.append('-h')
  if target_id:
    cmd.extend(['-t', target_id])

  # New pane size
  if lines:
    cmd.extend(['-l', str(lines)])
  elif percent:
    cmd.extend(['-p', str(percent)])

  # New pane action
  cmd.extend(prep_action(**action))

  # Run and return pane_id
  proc = run_program(cmd, check=False)
  return proc.stdout.strip()


def respawn_pane(pane_id, **action):
  """Respawn pane with action."""
  cmd = ['tmux', 'respawn-pane', '-k', '-t', pane_id]
  cmd.extend(prep_action(**action))

  # Respawn
  run_program(cmd, check=False)


def zoom_pane(pane_id=None):
  """Toggle zoom status for current or target pane."""
  cmd = ['tmux', 'resize-pane', '-Z']
  if pane_id:
    cmd.extend(['-t', pane_id])

  # Toggle
  run_program(cmd, check=False)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
