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
  parts = pathlib.Path(path).resolve().relative_to('/').parts
  real_path = '/'

  # Fix case
  for part in parts:
    real_path = case_insensitive_search(real_path, part)

  # Raise error if path doesn't exist
  path_obj = pathlib.Path(real_path)
  if not path_obj.exists():
    raise FileNotFoundError(path_obj)

  # Done
  return path_obj


def is_valid_main_kit(path_obj):
  """Verify PathObj contains the main kit, returns bool."""
  return path_obj.is_dir() and path_obj.joinpath('.bin').exists()


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
