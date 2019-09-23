"""WizardKit: Windows Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import pathlib
import re
import time

from wk import cfg
from wk.borrowed import acpi
from wk.exe import run_program
from wk.io import non_clobber_path
from wk.std import GenericError, GenericWarning, sleep


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
REG_MSISERVER = r'HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer'
SLMGR = pathlib.Path(f'{os.environ.get("SYSTEMROOT")}/System32/slmgr.vbs')


# Functions
def activate_with_bios():
  """Attempt to activate Windows with a key stored in the BIOS."""
  # Code borrowed from https://github.com/aeruder/get_win8key
  #####################################################
  #script to query windows 8.x OEM key from PC firmware
  #ACPI -> table MSDM -> raw content -> byte offset 56 to end
  #ck, 03-Jan-2014 (christian@korneck.de)
  #####################################################
  bios_key = None
  table = b"MSDM"
  if acpi.FindAcpiTable(table) is True:
    rawtable = acpi.GetAcpiTable(table)
    #http://msdn.microsoft.com/library/windows/hardware/hh673514
    #byte offset 36 from beginning
    #   = Microsoft 'software licensing data structure'
    #   / 36 + 20 bytes offset from beginning = Win Key
    bios_key = rawtable[56:len(rawtable)].decode("utf-8")
  if not bios_key:
    raise GenericError('BIOS key not found.')

  # Check if activation is needed
  if is_activated():
    raise GenericWarning('System already activated')

  # Install Key
  cmd = ['cscript', '//nologo', SLMGR, '/ipk', bios_key]
  run_program(cmd, check=False)
  sleep(5)

  # Attempt activation
  cmd = ['cscript', '//nologo', SLMGR, '/ato']
  run_program(cmd, check=False)
  sleep(5)

  # Check status
  if not is_activated():
    raise GenericError('Activation Failed')


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


def get_activation_string():
  """Get activation status, returns str."""
  cmd = ['cscript', '//nologo', SLMGR, '/xpr']
  result = run_program(cmd, check=False)
  act_str = result.stdout
  act_str = act_str.splitlines()[1]
  act_str = act_str.strip()
  return act_str


def is_activated():
  """Check if Windows is activated via slmgr.vbs and return bool."""
  act_str = get_activation_string()

  # Check result.
  return act_str and 'permanent' in act_str


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
