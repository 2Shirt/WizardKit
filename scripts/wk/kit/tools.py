"""WizardKit: Tool Functions"""
# vim: sts=2 sw=2 ts=2

import pathlib
import sys

from wk.exe import popen_program, run_program


# STATIC VARIABLES
ARCH = '64' if sys.maxsize > 2**32 else '32'


# "GLOBAL" VARIABLES
CACHED_DIRS = {}


# Functions
def find_kit_dir(name=None):
  """Find folder in kit, returns pathlib.Path.

  Search is performed in the script's path and then recursively upwards.
  If name is given then search for that instead."""
  cur_path = pathlib.Path(__file__).resolve().parent
  search = name if name else '.bin'

  # Search
  if name in CACHED_DIRS:
    return CACHED_DIRS[name]
  while not cur_path.match(cur_path.anchor):
    if cur_path.joinpath(search).exists():
      break
    cur_path = cur_path.parent

  # Check
  if cur_path.match(cur_path.anchor):
    raise FileNotFoundError(f'Failed to find kit dir, {name=}')
  if name:
    cur_path = cur_path.joinpath(name)

  # Done
  CACHED_DIRS[name] = cur_path
  return cur_path


def get_tool_path(folder, name):
  """Get tool path, returns pathlib.Path"""
  bin_dir = find_kit_dir('.bin')

  # "Search"
  tool_path = bin_dir.joinpath(f'{folder}/{name}{ARCH}.exe')
  if not tool_path.exists():
    tool_path = tool_path.with_stem(name)

  # Missing?
  if not tool_path.exists():
    raise FileNotFoundError(f'Failed to find tool, {folder=}, {name=}')

  # Done
  return tool_path


def run_tool(folder, name, *args, popen=False):
  """Run tool from kit."""
  cmd = [get_tool_path(folder, name), *args]
  proc = None

  # Run
  if popen:
    proc = popen_program(cmd)
  else:
    proc = run_program(cmd, check=False)

  # Done
  return proc


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
