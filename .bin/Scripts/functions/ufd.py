# Wizard Kit: Functions - UFD

import pathlib
from functions.common import *


def case_insensitive_search(path, item):
  """Search path for item case insensitively, returns str."""
  regex_match = '^{}$'.format(item)
  real_path = ''

  # Quick check first
  if os.path.exists('{}/{}'.format(path, item)):
    real_path = '{}{}{}'.format(
      path,
      '' if path == '/' else '/',
      item,
      )

  # Check all items in dir
  for entry in os.scandir(path):
    if re.match(regex_match, entry.name, re.IGNORECASE):
      real_path = '{}{}{}'.format(
        path,
        '' if path == '/' else '/',
        entry.name,
        )

  # Done
  if real_path:
    return real_path
  else:
    raise FileNotFoundError('{}/{}'.format(path, item))


def find_path(path):
  """Find path case-insensitively, returns pathlib.Path obj."""
  path_obj = pathlib.Path(path).resolve()

  # Quick check first
  if path_obj.exists():
    return path_obj

  # Fix case
  parts = path_obj.relative_to('/').parts
  real_path = '/'
  for part in parts:
    try:
      real_path = case_insensitive_search(real_path, part)
    except NotADirectoryError:
      # Reclassify error
      raise FileNotFoundError(path)

  # Raise error if path doesn't exist
  path_obj = pathlib.Path(real_path)
  if not path_obj.exists():
    raise FileNotFoundError(path_obj)

  # Done
  return path_obj


def is_valid_path(path_obj, path_type):
  """Verify path_obj is valid by type, returns bool."""
  valid_path = False
  if path_type == 'DIR':
    valid_path = path_obj.is_dir()
  elif path_type == 'KIT':
    valid_path = path_obj.is_dir() and path_obj.joinpath('.bin').exists()
  elif path_type == 'ISO':
    valid_path = path_obj.is_file() and path_obj.suffix.lower() == '.iso'
  elif path_type == 'UFD':
    valid_path = path_obj.is_block_device()

  return valid_path


def recursive_copy(source, dest, overwrite=True):
  """Copy source to dest recursively.

  NOTE: This uses rsync style source/dest syntax.
  If the source has a trailing slash then it's contents are copied,
  otherwise the source itself is copied.

  Examples assuming "ExDir/ExFile.txt" exists:
  recursive_copy("ExDir", "Dest/") results in "Dest/ExDir/ExFile.txt"
  recursive_copy("ExDir/", "Dest/") results in "Dest/ExFile.txt"

  NOTE 2: dest does not use find_path because it might not exist.
  """
  copy_contents = source.endswith('/')
  source = find_path(source)
  dest = pathlib.Path(dest).resolve().joinpath(source.name)
  os.makedirs(dest.parent, exist_ok=True)

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
      raise GenericError('Refusing to replace file with dir: {}'.format(dest))
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
      raise GenericError('Refusing to replace dir with file: {}'.format(dest))
    elif overwrite:
      # Dest file exists, deleting and replacing file
      os.remove(dest)
      shutil.copy2(source, dest)
    else:
      # Refusing to delete file when overwrite=False
      raise GenericError('Refusing to delete file: {}'.format(dest))


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
