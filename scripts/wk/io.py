"""WizardKit: I/O Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import pathlib
import re
import shutil


# STATIC VARIABLES
LOG = logging.getLogger(__name__)


# Functions
def case_insensitive_path(path):
  """Find path case-insensitively, returns pathlib.Path obj."""
  given_path = pathlib.Path(path).resolve()
  real_path = None

  # Quick check
  if given_path.exists():
    return given_path

  # Search for real path
  parts = list(given_path.parts)
  real_path = parts.pop(0)
  for part in parts:
    try:
      real_path = case_insensitive_search(real_path, part)
    except NotADirectoryError as err:
      # Reclassify error
      raise FileNotFoundError(given_path) from err
  real_path = pathlib.Path(real_path)

  # Done
  return real_path


def case_insensitive_search(path, item):
  """Search path for item case insensitively, returns pathlib.Path obj."""
  path = pathlib.Path(path).resolve()
  given_path = path.joinpath(item)
  real_path = None
  regex = fr'^{item}'

  # Quick check
  if given_path.exists():
    return given_path

  # Check all items in path
  for entry in os.scandir(path):
    if re.match(regex, entry.name, re.IGNORECASE):
      real_path = path.joinpath(entry.name)

  # Raise exception if necessary
  if not real_path:
    raise FileNotFoundError(given_path)

  # Done
  return real_path


def delete_empty_folders(path):
  """Recursively delete all empty folders in path."""
  LOG.debug('path: %s', path)

  # Delete empty subfolders first
  for item in os.scandir(path):
    if item.is_dir():
      delete_empty_folders(item.path)

  # Attempt to remove (top) path
  try:
    delete_folder(path, force=False)
  except OSError:
    # Assuming it's not empty
    pass


def delete_folder(path, force=False, ignore_errors=False):
  """Delete folder if empty or if forced.

  NOTE: Exceptions are not caught by this function,
        ignore_errors is passed to shutil.rmtree to allow partial deletions.
  """
  LOG.debug(
    'path: %s, force: %s, ignore_errors: %s',
    path, force, ignore_errors,
    )

  if force:
    shutil.rmtree(path, ignore_errors=ignore_errors)
  else:
    os.rmdir(path)


def delete_item(path, force=False, ignore_errors=False):
  """Delete file or folder, optionally recursively.

  NOTE: Exceptions are not caught by this function,
        ignore_errors is passed to delete_folder to allow partial deletions.
  """
  LOG.debug(
    'path: %s, force: %s, ignore_errors: %s',
    path, force, ignore_errors,
    )

  path = pathlib.Path(path)
  if path.is_dir():
    delete_folder(path, force=force, ignore_errors=ignore_errors)
  else:
    os.remove(path)


def non_clobber_path(path):
  """Update path as needed to non-existing path, returns pathlib.Path."""
  LOG.debug('path: %s', path)
  path = pathlib.Path(path)
  name = path.name
  new_path = None
  suffix = ''.join(path.suffixes)
  name = name.replace(suffix, '')

  # Bail early
  if not path.exists():
    return path

  # Find non-existant path
  for _i in range(1000):
    test_path = path.with_name(f'{name}_{_i}').with_suffix(suffix)
    if not test_path.exists():
      new_path = test_path
      break

  # Raise error if viable path not found
  if not new_path:
    raise FileExistsError(new_path)

  # Done
  LOG.debug('new path: %s', new_path)
  return new_path


def recursive_copy(source, dest, overwrite=False):
  """Copy source to dest recursively.

  NOTE: This uses rsync style source/dest syntax.
  If the source has a trailing slash then it's contents are copied,
  otherwise the source itself is copied.

  Examples assuming "ExDir/ExFile.txt" exists:
  recursive_copy("ExDir", "Dest/") results in "Dest/ExDir/ExFile.txt"
  recursive_copy("ExDir/", "Dest/") results in "Dest/ExFile.txt"

  NOTE 2: dest does not use find_path because it might not exist.
  """
  copy_contents = str(source).endswith(('/', '\\'))
  source = case_insensitive_path(source)
  dest = pathlib.Path(dest).resolve().joinpath(source.name)
  os.makedirs(dest.parent, exist_ok=True)

  # Recursively copy source to dest
  if source.is_dir():
    if copy_contents:
      # Trailing slash syntax
      for item in os.scandir(source):
        recursive_copy(item.path, dest.parent, overwrite=overwrite)
    elif not dest.exists():
      # No conflict, copying whole tree (no merging needed)
      shutil.copytree(source, dest)
    elif not dest.is_dir():
      # Refusing to replace file with dir
      raise FileExistsError(f'Refusing to replace file: {dest}')
    else:
      # Dest exists and is a dir, merge dirs
      for item in os.scandir(source):
        recursive_copy(item.path, dest, overwrite=overwrite)
  elif source.is_file():
    if not dest.exists():
      # No conflict, copying file
      shutil.copy2(source, dest)
    elif not dest.is_file():
      # Refusing to replace dir with file
      raise FileExistsError(f'Refusing to replace dir: {dest}')
    elif overwrite:
      # Dest file exists, deleting and replacing file
      os.remove(dest)
      shutil.copy2(source, dest)
    else:
      # Refusing to delete file when overwrite=False
      raise FileExistsError(f'Refusing to delete file: {dest}')


def rename_item(path, new_path):
  """Rename item, returns pathlib.Path."""
  path = pathlib.Path(path)
  return path.rename(new_path)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
