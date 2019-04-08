# Wizard Kit: Functions - UFD

import pathlib
from functions.common import *


def case_insensitive_search(path, item):
  """Search path for item case insensitively, returns str."""
  if os.path.exists('{}/{}'.format(path, item)):
    # Easy mode
    return '{}/{}'.format(path, item)

  # Check all items in dir
  for entry in os.scandir(path):
    if re.match(entry.name, item, re.IGNORECASE):
      return '{}/{}'.format(path, entry.name)

  # If we get here the item wasn't found
  raise FileNotFoundError('{}/{}'.format(path, item))


def find_source_item(source_dir, item):
  """Find item relative to source dir, returns str."""
  path = source_dir
  if item.startswith('/'):
    item = item[1:]

  for part in item.split('/'):
    path = case_insensitive_search(path, part)

  return path


def get_full_path(item):
  """Get full path to item, returns pathlib.Path obj."""
  path_obj = pathlib.Path(item).resolve()
  if not path_obj.exists():
    raise FileNotFoundError(path_obj)

  return path_obj


def is_valid_main_kit(path_obj):
  """Verify PathObj contains the main kit, returns bool."""
  return path_obj.is_dir() and path_obj.joinpath('.bin').exists()


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
