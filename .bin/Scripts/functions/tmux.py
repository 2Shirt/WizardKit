# Wizard Kit: Functions - tmux

from functions.common import *


def create_file(filepath):
  """Create file if it doesn't exist."""
  if not os.path.exists(filepath):
    with open(filepath, 'w') as f:
      f.write('')


def tmux_capture_pane(pane_id=None):
  """Capture text from target, or current, pane, returns str."""
  cmd = ['tmux', 'capture-pane', '-p']
  if pane_id:
    cmd.extend(['-t', pane_id])
  text = ''

  # Capture
  result = run_program(cmd, check=False, encoding='utf-8', errors='ignore')
  text = result.stdout

  # Done
  return str(text)


def tmux_get_pane_size(pane_id=None):
  """Get target, or current, pane size, returns tuple."""
  x = -1
  y = -1
  cmd = ['tmux', 'display', '-p']
  if pane_id:
    cmd.extend(['-t', pane_id])
  cmd.append('#{pane_width} #{pane_height}')

  # Run cmd and set x & y
  result = run_program(cmd, check=False)
  try:
    x, y = result.stdout.decode().strip().split()
    x = int(x)
    y = int(y)
  except Exception:
    # Ignore and return unrealistic values
    pass

  return (x, y)


def tmux_kill_all_panes(pane_id=None):
  """Kill all tmux panes except the active pane or pane_id if specified."""
  cmd = ['tmux', 'kill-pane', '-a']
  if pane_id:
    cmd.extend(['-t', pane_id])
  run_program(cmd, check=False)


def tmux_kill_pane(*panes):
  """Kill tmux pane by id."""
  cmd = ['tmux', 'kill-pane', '-t']
  for pane_id in panes:
    if not pane_id:
      # Skip empty strings, None values, etc
      continue
    run_program(cmd+[pane_id], check=False)


def tmux_poll_pane(pane_id):
  """Check if pane exists, returns bool."""
  cmd = ['tmux', 'list-panes', '-F', '#D']
  result = run_program(cmd, check=False)
  panes = result.stdout.decode().splitlines()
  return pane_id in panes


def tmux_resize_pane(pane_id=None, x=None, y=None, **kwargs):
  """Resize pane to specific hieght or width."""
  if not x and not y:
    raise Exception('Neither height nor width specified.')

  cmd = ['tmux', 'resize-pane']
  if pane_id:
    # NOTE: If pane_id not specified then the current pane will be resized
    cmd.extend(['-t', pane_id])
  if x:
    cmd.extend(['-x', str(x)])
  elif y:
    cmd.extend(['-y', str(y)])

  run_program(cmd, check=False)


def tmux_split_window(
    lines=None, percent=None,
    behind=False, vertical=False,
    follow=False, target_pane=None,
    command=None, working_dir=None,
    text=None, watch=None, watch_cmd='cat'):
  """Run tmux split-window command and return pane_id as str."""
  # Bail early
  if not lines and not percent:
    raise Exception('Neither lines nor percent specified.')
  if not command and not text and not watch:
    raise Exception('No command, text, or watch file specified.')

  # Build cmd
  cmd = ['tmux', 'split-window', '-PF', '#D']
  if behind:
    cmd.append('-b')
  if vertical:
    cmd.append('-v')
  else:
    cmd.append('-h')
  if not follow:
    cmd.append('-d')
  if lines is not None:
    cmd.extend(['-l', str(lines)])
  elif percent is not None:
    cmd.extend(['-p', str(percent)])
  if target_pane:
    cmd.extend(['-t', str(target_pane)])

  if working_dir:
    cmd.extend(['-c', working_dir])
  if command:
    cmd.extend(command)
  elif text:
    cmd.extend(['echo-and-hold "{}"'.format(text)])
  elif watch:
    create_file(watch)
    if watch_cmd == 'cat':
      cmd.extend([
        'watch', '--color', '--no-title',
        '--interval', '1',
        'cat', watch])
    elif watch_cmd == 'tail':
      cmd.extend(['tail', '-f', watch])

  # Run and return pane_id
  result = run_program(cmd)
  return result.stdout.decode().strip()


def tmux_update_pane(
    pane_id, command=None, working_dir=None,
    text=None, watch=None, watch_cmd='cat'):
  """Respawn with either a new command or new text."""
  # Bail early
  if not command and not text and not watch:
    raise Exception('No command, text, or watch file specified.')

  cmd = ['tmux', 'respawn-pane', '-k', '-t', pane_id]
  if working_dir:
    cmd.extend(['-c', working_dir])
  if command:
    cmd.extend(command)
  elif text:
    cmd.extend(['echo-and-hold "{}"'.format(text)])
  elif watch:
    create_file(watch)
    if watch_cmd == 'cat':
      cmd.extend([
        'watch', '--color', '--no-title',
        '--interval', '1',
        'cat', watch])
    elif watch_cmd == 'tail':
      cmd.extend(['tail', '-f', watch])

  run_program(cmd)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
