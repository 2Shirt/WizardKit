"""WizardKit: Windows Functions"""
# vim: sts=2 sw=2 ts=2

import logging
import os
import pathlib
import platform
import winreg

from contextlib import suppress

from wk.borrowed import acpi
from wk.exe import run_program
from wk.io import non_clobber_path
from wk.log import format_log_path
from wk.std import GenericError, GenericWarning, sleep


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
KNOWN_DATA_TYPES = {
  'BINARY': winreg.REG_BINARY,
  'DWORD': winreg.REG_DWORD,
  'DWORD_LITTLE_ENDIAN': winreg.REG_DWORD_LITTLE_ENDIAN,
  'DWORD_BIG_ENDIAN': winreg.REG_DWORD_BIG_ENDIAN,
  'EXPAND_SZ': winreg.REG_EXPAND_SZ,
  'LINK': winreg.REG_LINK,
  'MULTI_SZ': winreg.REG_MULTI_SZ,
  'NONE': winreg.REG_NONE,
  'QWORD': winreg.REG_QWORD,
  'QWORD_LITTLE_ENDIAN': winreg.REG_QWORD_LITTLE_ENDIAN,
  'SZ': winreg.REG_SZ,
  }
KNOWN_HIVES = {
  'HKCR': winreg.HKEY_CLASSES_ROOT,
  'HKCU': winreg.HKEY_CURRENT_USER,
  'HKLM': winreg.HKEY_LOCAL_MACHINE,
  'HKU': winreg.HKEY_USERS,
  'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
  'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
  'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
  'HKEY_USERS': winreg.HKEY_USERS,
  }
KNOWN_HIVE_NAMES = {
  winreg.HKEY_CLASSES_ROOT: 'HKCR',
  winreg.HKEY_CURRENT_USER: 'HKCU',
  winreg.HKEY_LOCAL_MACHINE: 'HKLM',
  winreg.HKEY_USERS: 'HKU',
  winreg.HKEY_CLASSES_ROOT: 'HKEY_CLASSES_ROOT',
  winreg.HKEY_CURRENT_USER: 'HKEY_CURRENT_USER',
  winreg.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE',
  winreg.HKEY_USERS: 'HKEY_USERS',
  }
OS_VERSION = float(platform.win32_ver()[0])
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
  proc = run_program(cmd, check=False)
  act_str = proc.stdout
  act_str = act_str.splitlines()[1]
  act_str = act_str.strip()
  return act_str


def is_activated():
  """Check if Windows is activated via slmgr.vbs and return bool."""
  act_str = get_activation_string()

  # Check result.
  return act_str and 'permanent' in act_str


def run_chkdsk_offline():
  """Set filesystem 'dirty bit' to force a CHKDSK during startup."""
  cmd = f'fsutil dirty set {os.environ.get("SYSTEMDRIVE")}'
  proc = run_program(cmd.split(), check=False)

  # Check result
  if proc.returncode > 0:
    raise GenericError('Failed to set dirty bit.')


def run_chkdsk_online():
  """Run CHKDSK in a split window.

  NOTE: If run on Windows 8+ online repairs are attempted.
  """
  cmd = ['CHKDSK', os.environ.get('SYSTEMDRIVE', 'C:')]
  if OS_VERSION >= 8:
    cmd.extend(['/scan', '/perf'])
  log_path = format_log_path(log_name='CHKDSK', tool=True)
  err_path = log_path.with_suffix('.err')

  # Run scan
  proc = run_program(cmd, check=False)

  # Check result
  if proc.returncode == 1:
    raise GenericWarning('Repaired (or manually aborted)')
  if proc.returncode > 1:
    raise GenericError('Issue(s) detected')

  # Save output
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'w') as _f:
    _f.write(proc.stdout)
  with open(err_path, 'w') as _f:
    _f.write(proc.stderr)


def run_sfc_scan():
  """Run SFC and save results."""
  cmd = ['sfc', '/scannow']
  log_path = format_log_path(log_name='SFC', tool=True)
  err_path = log_path.with_suffix('.err')

  # Run SFC
  proc = run_program(cmd, check=False, encoding='utf-16')

  # Fix paths
  log_path = non_clobber_path(log_path)
  err_path = non_clobber_path(err_path)

  # Save output
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'w') as _f:
    _f.write(proc.stdout)
  with open(err_path, 'w') as _f:
    _f.write(proc.stderr)

  # Check result
  if 'did not find any integrity violations' in proc.stdout:
    pass
  elif 'successfully repaired' in proc.stdout:
    raise GenericWarning('Repaired')
  elif 'found corrupt files' in proc.stdout:
    raise GenericError('Corruption detected')
  else:
    raise OSError


# Registry Functions
def reg_delete_key(hive, key, recurse=False):
  # pylint: disable=raise-missing-from
  """Delete a key from the registry.

  NOTE: If recurse is False then it will only work on empty keys.
  """
  hive = reg_get_hive(hive)
  hive_name = KNOWN_HIVE_NAMES.get(hive, '???')

  # Delete subkeys first
  if recurse:
    with suppress(WindowsError), winreg.OpenKey(hive, key) as open_key:
      while True:
        subkey = fr'{key}\{winreg.EnumKey(open_key, 0)}'
        reg_delete_key(hive, subkey, recurse=recurse)

  # Delete key
  try:
    winreg.DeleteKey(hive, key)
    LOG.warning(r'Deleting registry key: %s\%s', hive_name, key)
  except FileNotFoundError:
    # Ignore
    pass
  except PermissionError:
    LOG.error(r'Failed to delete registry key: %s\%s', hive_name, key)
    if recurse:
      # Re-raise exception
      raise

    # recurse is not True so assuming we tried to remove a non-empty key
    msg = fr'Refusing to remove non-empty key: {hive_name}\{key}'
    raise FileExistsError(msg)


def reg_delete_value(hive, key, value):
  """Delete a value from the registry."""
  access = winreg.KEY_ALL_ACCESS
  hive = reg_get_hive(hive)
  hive_name = KNOWN_HIVE_NAMES.get(hive, '???')

  # Delete value
  with winreg.OpenKey(hive, key, access=access) as open_key:
    try:
      winreg.DeleteValue(open_key, value)
      LOG.warning(
        r'Deleting registry value: %s\%s "%s"', hive_name, key, value,
        )
    except FileNotFoundError:
      # Ignore
      pass
    except PermissionError:
      LOG.error(
        r'Failed to delete registry value: %s\%s "%s"', hive_name, key, value,
        )
      # Re-raise exception
      raise


def reg_get_hive(hive):
  """Get winreg HKEY constant from string, returns HKEY constant."""
  if isinstance(hive, int):
    # Assuming we're already a winreg HKEY constant
    pass
  else:
    hive = KNOWN_HIVES[hive.upper()]

  # Done
  return hive


def reg_get_data_type(data_type):
  """Get registry data type from string, returns winreg constant."""
  if isinstance(data_type, int):
    # Assuming we're already a winreg value type constant
    pass
  else:
    data_type = KNOWN_DATA_TYPES[data_type.upper()]

  # Done
  return data_type


def reg_key_exists(hive, key):
  """Test if the specified hive/key exists, returns bool."""
  exists = False
  hive = reg_get_hive(hive)

  # Query key
  try:
    winreg.QueryValue(hive, key)
  except FileNotFoundError:
    # Leave set to False
    pass
  else:
    exists = True

  # Done
  return exists


def reg_read_value(hive, key, value, force_32=False, force_64=False):
  """Query value from hive/hey, returns multiple types."""
  access = winreg.KEY_READ
  data = None
  hive = reg_get_hive(hive)

  # Set access
  if force_32:
    access = access | winreg.KEY_WOW64_32KEY
  elif force_64:
    access = access | winreg.KEY_WOW64_64KEY

  # Query value
  with winreg.OpenKey(hive, key, access=access) as open_key:
    # Returning first part of tuple and ignoreing type
    data = winreg.QueryValueEx(open_key, value)[0]

  # Done
  return data


def reg_write_settings(settings):
  """Set registry values in bulk from a custom data structure.

  Data structure should be as follows:
  EXAMPLE_SETTINGS = {
    # See KNOWN_HIVES for valid hives
    'HKLM': {
      r'Software\\2Shirt\\WizardKit': (
        # Value tuples should be in the form:
        # (name, data, data-type, option),
        # See KNOWN_DATA_TYPES for valid types
        # The option item is optional
        ('Sample Value #1', 'Sample Data', 'SZ'),
        ('Sample Value #2', 14, 'DWORD'),
        ),
      # An empty key will be created if no values are specified
      r'Software\\2Shirt\\WizardKit\\Empty': (),
      r'Software\\2Shirt\\WizardKit\\Test': (
        ('Sample Value #3', 14000000000000, 'QWORD'),
        ),
      },
    'HKCU': {
      r'Software\\2Shirt\\WizardKit': (
        # The 4th item forces using the 32-bit registry
        # See reg_set_value() for valid options
        ('Sample Value #4', 'Sample Data', 'SZ', '32'),
        ),
      },
    }
  """
  for hive, keys in settings.items():
    hive = reg_get_hive(hive)
    for key, values in keys.items():
      if not values:
        # Create an empty key
        winreg.CreateKey(hive, key)
      for value in values:
        reg_set_value(hive, key, *value)


def reg_set_value(hive, key, name, data, data_type, option=None):
  # pylint: disable=too-many-arguments
  """Set value for hive/key."""
  access = winreg.KEY_WRITE
  data_type = reg_get_data_type(data_type)
  hive = reg_get_hive(hive)
  option = str(option)

  # Safety check
  if not name and option in ('32', '64'):
    raise NotImplementedError(
      'Unable to set default values using alternate registry views',
      )

  # Set access
  if option == '32':
    access = access | winreg.KEY_WOW64_32KEY
  elif option == '64':
    access = access | winreg.KEY_WOW64_64KEY

  # Create key
  winreg.CreateKeyEx(hive, key, access=access)

  # Set value
  if name:
    with winreg.OpenKey(hive, key, access=access) as open_key:
      winreg.SetValueEx(open_key, name, 0, data_type, data)
  else:
    # Set default value instead
    winreg.SetValue(hive, key, data_type, data)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
