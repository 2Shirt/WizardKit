"""WizardKit: Windows Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import pathlib
import re
import time

from wk import cfg
from wk.exe import run_program
from wk.io import non_clobber_path
from wk.std import GenericError, GenericWarning

# STATIC VARIABLES
LOG = logging.getLogger(__name__)
REG_MSISERVER = r'HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer'


# Functions
def disable_safemode():
  """Edit BCD to remove safeboot value."""
  cmd = ['bcdedit', '/deletevalue', '{default}', 'safeboot']
  run_program(cmd)


def disable_safemode_msi():
  """Disable MSI access under safemode."""
  cmd = ['reg', 'delete', REG_MSISERVER, '/f']
  run_program(cmd)


def enable_safemode():
  """Edit BCD to set safeboot as default."""
  cmd = ['bcdedit', '/set', '{default}', 'safeboot', 'network']
  run_program(cmd)


def enable_safemode_msi():
  """Enable MSI access under safemode."""
  cmd = ['reg', 'add', REG_MSISERVER, '/f']
  run_program(cmd)
  cmd = [
    'reg', 'add', REG_MSISERVER, '/ve',
    '/t', 'REG_SZ',
    '/d', 'Service', '/f',
    ]
  run_program(cmd)


def run_sfc_scan():
  """Run SFC and save results."""
  cmd = ['sfc', '/scannow']
  log_path = pathlib.Path(
    '{drive}/{short}/Logs/{date}/Tools/SFC.log'.format(
      drive=os.environ.get('SYSTEMDRIVE', 'C:'),
      short=cfg.main.KIT_NAME_SHORT,
      date=time.strftime('%Y-%m-%d'),
      ))
  err_path = log_path.with_suffix('.err')

  # Run SFC
  proc = run_program(cmd, check=False)

  # Fix paths
  log_path = non_clobber_path(log_path)
  err_path = non_clobber_path(err_path)

  # Save output
  output = proc.stdout.replace('\0', '')
  errors = proc.stderr.replace('\0', '')
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'w') as _f:
    _f.write(output)
  with open(err_path, 'w') as _f:
    _f.write(errors)

  # Check result
  if re.findall(r'did\s+not\s+find\s+any\s+integrity\s+violations', output):
    pass
  elif re.findall(r'successfully\s+repaired\s+them', output):
    raise GenericWarning('Repaired')
  else:
    raise GenericError


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
