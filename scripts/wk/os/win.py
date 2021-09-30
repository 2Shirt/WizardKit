"""WizardKit: Windows Functions"""
# vim: sts=2 sw=2 ts=2

import ctypes
import logging
import os
import pathlib
import platform

from contextlib import suppress
import psutil

try:
  import winreg
except ImportError as err:
  if platform.system() == 'Windows':
    raise err

from wk.borrowed import acpi
from wk.cfg.main import KIT_NAME_FULL
from wk.cfg.windows_builds import (
  OLDEST_SUPPORTED_BUILD,
  OUTDATED_BUILD_NUMBERS,
  WINDOWS_BUILDS,
  )
from wk.exe import get_json_from_command, run_program
from wk.kit.tools import find_kit_dir
from wk.std import (
  GenericError,
  GenericWarning,
  bytes_to_string,
  color_string,
  sleep,
  )


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
ARCH = '64' if platform.architecture()[0] == '64bit' else '32'
CONEMU = 'ConEmuPID' in os.environ
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
RAM_OK      = 5.5 * 1024**3 # ~6 GiB assuming a bit of shared memory
RAM_WARNING = 3.5 * 1024**3 # ~4 GiB assuming a bit of shared memory
REG_MSISERVER = r'HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network\MSIServer'
SLMGR = pathlib.Path(f'{os.environ.get("SYSTEMROOT")}/System32/slmgr.vbs')


# Activation Functions
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
  # Check if activation is needed
  if is_activated():
    raise GenericWarning('System already activated')

  # Get BIOS key
  if acpi.FindAcpiTable(table) is True:
    rawtable = acpi.GetAcpiTable(table)
    #http://msdn.microsoft.com/library/windows/hardware/hh673514
    #byte offset 36 from beginning
    #   = Microsoft 'software licensing data structure'
    #   / 36 + 20 bytes offset from beginning = Win Key
    bios_key = rawtable[56:len(rawtable)].decode("utf-8")
  if not bios_key:
    raise GenericError('BIOS key not found.')

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


# Date / Time functions
def get_timezone():
  """Get current timezone using tzutil, returns str."""
  cmd = ['tzutil', '/g']
  proc = run_program(cmd, check=False)
  return proc.stdout


def set_timezone(zone):
  """Set current timezone using tzutil."""
  cmd = ['tzutil', '/s', zone]
  run_program(cmd, check=False)


# Info Functions
def check_4k_alignment(show_alert=False):
  """Check if all partitions are 4K aligned, returns book."""
  cmd = ['WMIC', 'partition', 'get', 'StartingOffset']

  # Check offsets
  proc = run_program(cmd)
  for offset in proc.stdout.splitlines():
    offset = offset.strip()
    if not offset.isnumeric():
      continue
    if int(offset) % 4096 != 0:
      # Not aligned
      if show_alert:
        show_alert_box('One or more partitions are not 4K aligned')
      raise GenericError('One or more partitions are not 4K aligned')


def get_installed_antivirus():
  """Get list of installed antivirus programs, returns list."""
  cmd = [
    'WMIC', r'/namespace:\\root\SecurityCenter2',
    'path', 'AntivirusProduct',
    'get', 'displayName', '/value',
    ]
  products = []
  report = []

  # Get list of products
  proc = run_program(cmd)
  for line in proc.stdout.splitlines():
    line = line.strip()
    if '=' in line:
      products.append(line.split('=')[1])

  # Check product(s) status
  for product in sorted(products):
    cmd = [
      'WMIC', r'/namespace:\\root\SecurityCenter2',
      'path', 'AntivirusProduct',
      'where', f'displayName="{product}"',
      'get', 'productState', '/value',
      ]
    proc = run_program(cmd)
    state = proc.stdout.split('=')[1]
    state = hex(int(state))
    if str(state)[3:5] not in ['10', '11']:
      report.append(color_string(f'[Disabled] {product}', 'YELLOW'))
    else:
      report.append(product)

  # Final check
  if not report:
    report.append(color_string('No products detected', 'RED'))

  # Done
  return report


def get_installed_ram(as_list=False, raise_exceptions=False):
  """Get installed RAM."""
  mem = psutil.virtual_memory()
  mem_str = bytes_to_string(mem.total, decimals=1)

  # Raise exception if necessary
  if raise_exceptions:
    if RAM_OK > mem.total >= RAM_WARNING:
      raise GenericWarning(mem_str)
    if mem.total > RAM_WARNING:
      raise GenericError(mem_str)

  # Done
  return [mem_str] if as_list else mem_str


def get_os_activation(as_list=False, check=True):
  """Get OS activation status, returns str.

  NOTE: If check=True then raise an exception if OS isn't activated.
  """
  act_str = get_activation_string()

  if check and not is_activated():
    if 'unavailable' in act_str.lower():
      raise GenericWarning(act_str)
    # Else
    raise GenericError(act_str)

  # Done
  return [act_str] if as_list else act_str


def get_os_name(as_list=False, check=True):
  """Build OS display name, returns str.

  NOTE: If check=True then an exception is raised if the OS version is
        outdated or unsupported.
  """
  key = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
  build_version = int(reg_read_value("HKLM", key, "CurrentBuild"))
  build_version_full = platform.win32_ver()[1]
  details = WINDOWS_BUILDS.get(build_version_full, f'Build {build_version}')
  display_name = (
    f'{reg_read_value("HKLM", key, "ProductName")} {ARCH}-bit {details}'
    )

  # Check for support issues
  if check:
    if build_version in OUTDATED_BUILD_NUMBERS:
      raise GenericWarning(f'{display_name} (outdated)')

    if build_version < OLDEST_SUPPORTED_BUILD:
      raise GenericError(f'{display_name} (unsupported)')

  # Done
  return [display_name] if as_list else display_name


def get_raw_disks():
  """Get all disks without a partiton table, returns list."""
  script_path = find_kit_dir('Scripts').joinpath('get_raw_disks.ps1')
  cmd = ['PowerShell', '-ExecutionPolicy', 'Bypass', '-File', script_path]
  json_data = get_json_from_command(cmd)
  raw_disks = []

  # Fix JSON if only one disk was detected
  if isinstance(json_data, dict):
    json_data = [json_data]

  # Parse JSON
  for disk in json_data:
    size_str = bytes_to_string(int(disk["Size"]), use_binary=False)
    raw_disks.append(f'{disk["FriendlyName"]} ({size_str})')

  # Done
  return raw_disks


def get_volume_usage(use_colors=False):
  """Get space usage info for all fixed volumes, returns list."""
  report = []
  for disk in psutil.disk_partitions():
    if 'fixed' not in disk.opts:
      continue
    total, _, free, percent = psutil.disk_usage(disk.device)
    color = None
    if percent > 85:
      color = 'RED'
    elif percent > 75:
      color = 'YELLOW'
    display_str = (
      f'{free/total:>5.2f}% Free'
      f'  ({bytes_to_string(free, 2):>10} / {bytes_to_string(total, 2):>10})'
      )
    if use_colors:
      display_str = color_string(display_str, color)
    report.append(f'{disk.device}  {display_str}')

  # Done
  return report


def show_alert_box(message, title=None):
  """Show Windows alert box with message."""
  title = title if title else f'{KIT_NAME_FULL} Warning'
  message_box = ctypes.windll.user32.MessageBoxW
  message_box(None, message, title, 0x00001030)


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
    with suppress(OSError), winreg.OpenKey(hive, key) as open_key:
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
  """Query value from hive/hey, returns multiple types.

  NOTE: Set value='' to read the default value.
  """
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


# Safe Mode Functions
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


# Secure Boot Functions
def is_booted_uefi():
  """Check if booted UEFI or legacy, returns bool."""
  kernel = ctypes.windll.kernel32
  firmware_type = ctypes.c_uint()

  # Get value from kernel32 API (firmware_type is updated by the call)
  try:
    kernel.GetFirmwareType(ctypes.byref(firmware_type))
  except Exception: # pylint: disable=broad-except
    # Ignore and set firmware_type back to zero
    firmware_type = ctypes.c_uint(0)

  # Check result
  return firmware_type.value == 2


def is_secure_boot_enabled(raise_exceptions=False, show_alert=False):
  """Check if Secure Boot is enabled, returns bool.

  If raise_exceptions is True then an exception is raised with details.
  If show_alert is True a popup alert box is shown if it's not enabled.
  """
  booted_uefi = is_booted_uefi()
  cmd = ['PowerShell', '-Command', 'Confirm-SecureBootUEFI']
  enabled = False
  msg_error = None
  msg_warning = None

  # Bail early
  if OS_VERSION < 8:
    if raise_exceptions:
      raise GenericWarning(f'Secure Boot not available for {OS_VERSION}')
    return False

  # Check results
  proc = run_program(cmd, check=False)
  if proc.returncode:
    # Something went wrong
    if booted_uefi:
      msg_warning = 'UNKNOWN'
    else:
      msg_warning = 'DISABLED\n\nOS installed LEGACY'
  else:
    # Command completed
    enabled = 'True' in proc.stdout
    if 'False' in proc.stdout:
      msg_error = 'ERROR'
    else:
      msg_warning = 'UNKNOWN'

  # Show popup and/or raise exceptions as necessary
  for msg, exc in ((msg_error, GenericError), (msg_warning, GenericWarning)):
    if not msg:
      continue
    msg = f'Secure Boot {msg}'
    if show_alert:
      show_alert_box(msg)
    if raise_exceptions:
      raise exc(msg)
    break

  # Done
  return enabled


# Service Functions
def disable_service(service_name):
  """Set service startup to disabled."""
  cmd = ['sc', 'config', service_name, 'start=', 'disabled']
  run_program(cmd, check=False)

  # Verify service was disabled
  if get_service_start_type(service_name) != 'disabled':
    raise GenericError(f'Failed to disable service {service_name}')


def enable_service(service_name, start_type='auto'):
  """Enable service by setting start type."""
  cmd = ['sc', 'config', service_name, 'start=', start_type]
  psutil_type = 'automatic'
  if start_type == 'demand':
    psutil_type = 'manual'

  # Enable service
  run_program(cmd, check=False)

  # Verify service was enabled
  if get_service_start_type(service_name) != psutil_type:
    raise GenericError(f'Failed to enable service {service_name}')


def get_service_status(service_name):
  """Get service status using psutil, returns str."""
  status = 'unknown'
  try:
    service = psutil.win_service_get(service_name)
    status = service.status()
  except psutil.NoSuchProcess:
    status = 'missing?'

  return status


def get_service_start_type(service_name):
  """Get service startup type using psutil, returns str."""
  start_type = 'unknown'
  try:
    service = psutil.win_service_get(service_name)
    start_type = service.start_type()
  except psutil.NoSuchProcess:
    start_type = 'missing?'

  return start_type


def start_service(service_name):
  """Stop service."""
  cmd = ['net', 'start', service_name]
  run_program(cmd, check=False)

  # Verify service was started
  if not get_service_status(service_name) in ('running', 'start_pending'):
    raise GenericError(f'Failed to start service {service_name}')


def stop_service(service_name):
  """Stop service."""
  cmd = ['net', 'stop', service_name]
  run_program(cmd, check=False)

  # Verify service was stopped
  if not get_service_status(service_name) == 'stopped':
    raise GenericError(f'Failed to stop service {service_name}')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
