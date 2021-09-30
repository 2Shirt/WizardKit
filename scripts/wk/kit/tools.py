"""WizardKit: Tool Functions"""
# vim: sts=2 sw=2 ts=2

from datetime import datetime, timedelta
import logging
import pathlib
import platform

import requests

from wk.cfg.main import ARCHIVE_PASSWORD
from wk.cfg.sources import DOWNLOAD_FREQUENCY, SOURCES
from wk.exe import popen_program, run_program
from wk.std import GenericError


# STATIC VARIABLES
ARCH = '64' if platform.architecture()[0] == '64bit' else '32'
LOG = logging.getLogger(__name__)


# "GLOBAL" VARIABLES
CACHED_DIRS = {}


# Functions
def download_file(out_path, source_url, as_new=False, overwrite=False):
  """Download a file using requests, returns pathlib.Path."""
  out_path = pathlib.Path(out_path).resolve()
  name = out_path.name
  download_failed = None
  download_msg = f'Downloading {name}...'
  if as_new:
    out_path = out_path.with_suffix(f'{out_path.suffix}.new')
  print(download_msg, end='', flush=True)

  # Avoid clobbering
  if out_path.exists() and not overwrite:
    raise FileExistsError(f'Refusing to clobber {out_path}')

  # Create destination directory
  out_path.parent.mkdir(parents=True, exist_ok=True)

  # Request download
  try:
    response = requests.get(source_url, stream=True)
  except requests.RequestException as _err:
    download_failed = _err
  else:
    if not response.ok:
      download_failed = response

  # Download failed
  if download_failed:
    LOG.error('Failed to download file: %s', download_failed)
    raise GenericError(f'Failed to download file: {name}')

  # Write to file
  with open(out_path, 'wb') as _f:
    for chunk in response.iter_content(chunk_size=128):
      _f.write(chunk)

  # Done
  print(f'\033[{len(download_msg)}D\033[0K', end='', flush=True)
  return out_path


def download_tool(folder, name, suffix=None):
  """Download tool."""
  name_arch = f'{name}{ARCH}'
  out_path = get_tool_path(folder, name, check=False, suffix=suffix)
  up_to_date = False

  # Check if tool is up to date
  try:
    ctime = datetime.fromtimestamp(out_path.stat().st_ctime)
    up_to_date = datetime.now() - ctime < timedelta(days=DOWNLOAD_FREQUENCY)
  except FileNotFoundError:
    # Ignore - we'll download it below
    pass
  if out_path.exists() and up_to_date:
    LOG.info('Skip downloading up-to-date tool: %s', name)
    return

  # Get ARCH specific URL if available
  if name_arch in SOURCES:
    source_url = SOURCES[name_arch]
    out_path = out_path.with_name(f'{name_arch}{out_path.suffix}')
  else:
    source_url = SOURCES[name]

  # Download
  LOG.info('Downloading tool: %s', name)
  try:
    new_file = download_file(out_path, source_url, as_new=True)
    new_file.replace(out_path)
  except GenericError:
    # Ignore as long as there's still a version present
    if not out_path.exists():
      raise


def extract_archive(archive, out_path, *args, mode='x', silent=True):
  """Extract an archive to out_path."""
  out_path = pathlib.Path(out_path).resolve()
  out_path.parent.mkdir(parents=True, exist_ok=True)
  cmd = [get_tool_path('7-Zip', '7za'), mode, archive, f'-o{out_path}', *args]
  if silent:
    cmd.extend(['-bso0', '-bse0', '-bsp0'])

  # Extract
  run_program(cmd)


def extract_tool(folder):
  """Extract tool."""
  extract_archive(
    find_kit_dir('.cbin').joinpath(folder).with_suffix('.7z'),
    find_kit_dir('.bin').joinpath(folder),
    '-aos', f'-p{ARCHIVE_PASSWORD}',
    )


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


def get_tool_path(folder, name, check=True, suffix=None):
  """Get tool path, returns pathlib.Path"""
  bin_dir = find_kit_dir('.bin')
  if not suffix:
    suffix = 'exe'
  name_arch = f'{name}{ARCH}'

  # "Search"
  tool_path = bin_dir.joinpath(f'{folder}/{name_arch}.{suffix}')
  if not (tool_path.exists() or name_arch in SOURCES):
    # Use "default" path instead
    tool_path = tool_path.with_name(f'{name}.{suffix}')

  # Missing?
  if check and not tool_path.exists():
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
    extract_tool(folder)

  # Download tool
  if download:
    download_tool(folder, name)

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
