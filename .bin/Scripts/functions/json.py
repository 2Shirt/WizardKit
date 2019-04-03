# Wizard Kit: Functions - JSON

import json

from functions.common import *

def get_json_from_command(cmd, ignore_errors=True):
  """Capture JSON content from cmd output, returns dict.

  If the data can't be decoded then either an exception is raised
  or an empty dict is returned depending on ignore_errors.
  """
  errors = 'strict'
  json_data = {}

  if ignore_errors:
    errors = 'ignore'

  try:
    result = run_program(cmd, encoding='utf-8', errors=errors)
    json_data = json.loads(result.stdout)
  except (subprocess.CalledProcessError, json.decoder.JSONDecodeError):
    if not ignore_errors:
      raise

  return json_data


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
