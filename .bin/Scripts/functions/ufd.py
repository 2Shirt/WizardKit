# Wizard Kit: Functions - UFD

import pathlib
from functions.common import *


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
