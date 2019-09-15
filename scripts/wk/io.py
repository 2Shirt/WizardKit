'''WizardKit: I/O Functions'''
# vim: sts=2 sw=2 ts=2

import os
import shutil

import pathlib


# Functions
def delete_empty_folders(path):
  """Recursively delete all empty folders in path."""
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


def delete_folder(path, force=False):
  """Delete folder if empty or if forced."""
  if force:
    shutil.rmtree(path)
  else:
    os.rmdir(path)


def non_clobbering_path(path):
  """Update path as needed to non-existing path, returns pathlib.Path."""
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
    new_path = path.with_name(f'{name}_{_i}').with_suffix(suffix)
    if not new_path.exists():
      break

  # Raise error if viable path not found
  if not new_path:
    raise FileExistsError(new_path)

  # Done
  return new_path


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
