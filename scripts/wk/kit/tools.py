"""WizardKit: Tool Functions"""
# vim: sts=2 sw=2 ts=2

from datetime import datetime, timedelta
import logging
import pathlib
import sys

import requests

from wk.cfg.main import ARCHIVE_PASSWORD
from wk.cfg.tools import SOURCES, DOWNLOAD_FREQUENCY
from wk.exe import popen_program, run_program
from wk.std import GenericError


# STATIC VARIABLES
ARCH = '64' if sys.maxsize > 2**32 else '32'
LOG = logging.getLogger(__name__)


# "GLOBAL" VARIABLES
CACHED_DIRS = {}


# Functions
def download_file(out_path, source_url):
  """Download a file using requests."""
  out_path = pathlib.Path(out_path).resolve()
  out_path.parent.mkdir(parents=True, exist_ok=True)

  # Request download
  response = requests.get(source_url, stream=True)
  if not response.ok:
    LOG.error(
      'Failed to download file (status %s): %s',
      response.status_code, out_path.name,
      )
    raise GenericError(f'Failed to download file: {out_path.name}')

  # Write to file
  with open(out_path, 'wb') as _f:
    for chunk in response.iter_content(chunk_size=128):
      _f.write(chunk)

  # Done
  return out_path


def extract_archive(archive, out_path, *args, mode='x', silent=True):
  """Extract an archive to out_path."""
  out_path = pathlib.Path(out_path).resolve()
  out_path.parent.mkdir(parents=True, exist_ok=True)
  cmd = [get_tool_path('7-Zip', '7za'), mode, archive, f'-o{out_path}', *args]
  if silent:
    cmd.extend(['-bso0', '-bse0', '-bsp0'])

  # Extract
  run_program(cmd)


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


def run_tool(
    folder, name, *run_args,
    cbin=False, cwd=False, download=False, popen=False,
    **run_kwargs,
    ):
  """Run tool from the kit or the Internet, returns proc obj.

  proc will be either subprocess.CompletedProcess or subprocess.Popen."""
  proc = None

  # Extract from .cbin
  if cbin:
    extract_archive(
      find_kit_dir('.cbin').joinpath(folder).with_suffix('.7z'),
      find_kit_dir('.bin').joinpath(folder),
      '-aos', f'-p{ARCHIVE_PASSWORD}',
      )

  # Download tool
  if download:
    out_path = find_kit_dir('.bin').joinpath(f'{folder}/{name}.exe')
    outdated = False
    try:
      mod_time = datetime.fromtimestamp(out_path.stat().st_ctime)
      outdated = datetime.now() - mod_time > timedelta(days=DOWNLOAD_FREQUENCY)
    except FileNotFoundError:
      # Ignore and download
      pass
    if not out_path.exists() or outdated:
      LOG.info('Downloading tool: %s', name)
      source_url = SOURCES[name]
      download_file(out_path, source_url)
    else:
      LOG.info('Skip downloading tool: %s', name)

  # Run
  tool_path = get_tool_path(folder, name)
  cmd = [tool_path, *run_args]
  if cwd:
    run_kwargs['cwd'] = tool_path.parent
  if popen:
    proc = popen_program(cmd, **run_kwargs)
  else:
    proc = run_program(cmd, check=False, **run_kwargs)

  # Done
  return proc


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
