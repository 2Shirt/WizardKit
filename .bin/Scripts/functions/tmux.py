# Wizard Kit: Functions - tmux

from functions.common import *

def tmux_kill_pane(*panes):
  """Kill tmux pane by id."""
  cmd = ['tmux', 'kill-pane', '-t']
  for pane_id in panes:
    print(pane_id)
    run_program(cmd+[pane_id], check=False)

def tmux_poll_pane(pane_id):
  """Check if pane exists, returns bool."""
  cmd = ['tmux', 'list-panes', '-F', '#D']
  result = run_program(cmd, check=False)
  panes = result.stdout.decode().splitlines()
  return pane_id in panes

def tmux_split_window(
    lines=None, percent=None,
    behind=False, vertical=False,
    follow=False, target_pane=None,
    command=None, text=None, watch=None):
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

  if command:
    cmd.extend(command)
  elif text:
    cmd.extend(['echo-and-hold "{}"'.format(text)])
  elif watch:
    cmd.extend([
      'watch', '--color', '--no-title',
      '--interval', '1',
      'cat', watch])

  # Run and return pane_id
  result = run_program(cmd)
  return result.stdout.decode().strip()

def tmux_update_pane(pane_id, command=None, text=None):
  """Respawn with either a new command or new text."""
  # Bail early
  if not command and not text:
    raise Exception('Neither command nor text specified.')

  cmd = ['tmux', 'respawn-pane', '-k', '-t', pane_id]
  if command:
    cmd.extend(command)
  elif text:
    cmd.extend(['echo-and-hold "{}"'.format(text)])

  run_program(cmd)

if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
