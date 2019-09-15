'''WizardKit: I/O Functions'''
# vim: sts=2 sw=2 ts=2

import pathlib


# Functions
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
