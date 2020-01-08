# Wizard Kit: Functions - Common

import os
import psutil
import re
import shutil
import subprocess
import sys
import time
import traceback
try:
  import winreg
except ModuleNotFoundError:
  if psutil.WINDOWS:
    raise

from settings.main import *
from settings.tools import *
from settings.windows_builds import *
from subprocess import CalledProcessError


# Global variables
global_vars = {}


# STATIC VARIABLES
COLORS = {
  'CLEAR':  '\033[0m',
  'RED':    '\033[31m',
  'ORANGE': '\033[31;1m',
  'GREEN':  '\033[32m',
  'YELLOW': '\033[33m',
  'BLUE':   '\033[34m',
  'PURPLE': '\033[35m',
  'CYAN':   '\033[36m',
  }
try:
  HKU =  winreg.HKEY_USERS
  HKCR = winreg.HKEY_CLASSES_ROOT
  HKCU = winreg.HKEY_CURRENT_USER
  HKLM = winreg.HKEY_LOCAL_MACHINE
except NameError:
  if psutil.WINDOWS:
    raise


# Error Classes
class BIOSKeyNotFoundError(Exception):
  pass

class BinNotFoundError(Exception):
  pass

class GenericAbort(Exception):
  pass

class GenericError(Exception):
  pass

class GenericRepair(Exception):
  pass

class MultipleInstallationsError(Exception):
  pass

class NoProfilesError(Exception):
  pass

class Not4KAlignedError(Exception):
  pass

class NotInstalledError(Exception):
  pass

class OSInstalledLegacyError(Exception):
  pass

class PathNotFoundError(Exception):
  pass

class UnsupportedOSError(Exception):
  pass

class SecureBootDisabledError(Exception):
  pass

class SecureBootNotAvailError(Exception):
  pass

class SecureBootUnknownError(Exception):
  pass

class WindowsOutdatedError(Exception):
  pass

class WindowsUnsupportedError(Exception):
  pass


# General functions
def exit_script(return_value=0):
  """Exits the script after some cleanup and opens the log (if set)."""
  # Remove dirs (if empty)
  for dir in ['BackupDir', 'LogDir', 'TmpDir']:
    try:
      os.rmdir(global_vars[dir])
    except Exception:
      pass

  # Open Log (if it exists)
  log = global_vars.get('LogFile', '')
  if log and os.path.exists(log) and psutil.WINDOWS and ENABLED_OPEN_LOGS:
    try:
      extract_item('NotepadPlusPlus', silent=True)
      popen_program(
        [global_vars['Tools']['NotepadPlusPlus'],
        global_vars['LogFile']])
    except Exception:
      print_error('ERROR: Failed to extract Notepad++ and open log.')
      pause('Press Enter to exit...')

  # Kill Caffeine if still running
  kill_process('caffeine.exe')

  # Exit
  sys.exit(return_value)


def extract_item(item, filter='', silent=False):
  """Extract item from .cbin into .bin."""
  cmd = [
    global_vars['Tools']['SevenZip'], 'x', '-aos', '-bso0', '-bse0',
    '-p{ArchivePassword}'.format(**global_vars),
    r'-o{BinDir}\{item}'.format(item=item, **global_vars),
    r'{CBinDir}\{item}.7z'.format(item=item, **global_vars),
    filter]
  if not silent:
    print_standard('Extracting "{item}"...'.format(item=item))
  try:
    run_program(cmd)
  except FileNotFoundError:
    if not silent:
      print_warning('WARNING: Archive not found')
  except subprocess.CalledProcessError:
    if not silent:
      print_warning('WARNING: Errors encountered while exctracting data')


def get_process(name=None):
  """Get process by name, returns psutil.Process obj."""
  proc = None
  if not name:
    raise GenericError

  for p in psutil.process_iter():
    try:
      if p.name() == name:
        proc = p
    except psutil._exceptions.NoSuchProcess:
      # Process finished during iteration? Going to ignore
      pass
  return proc


def get_ticket_number():
  """Get TicketNumber from user, save in LogDir, and return as str."""
  if not ENABLED_TICKET_NUMBERS:
    return None
  ticket_number = None
  while ticket_number is None:
    _input = input('Enter ticket number: ')
    if re.match(r'^([0-9]+([-_]?\w+|))$', _input):
      ticket_number = _input
      out_file = r'{}\TicketNumber'.format(global_vars['LogDir'])
      if not psutil.WINDOWS:
        out_file = out_file.replace('\\', '/')
      with open(out_file, 'w', encoding='utf-8') as f:
        f.write(ticket_number)
  return ticket_number


def kill_process(name):
  """Kill any running caffeine.exe processes."""
  for proc in psutil.process_iter():
    if proc.name() == name:
      proc.kill()


def stay_awake():
  """Prevent the system from sleeping or hibernating."""
  # DISABLED due to VCR2008 dependency
  return
  # Bail if caffeine is already running
  for proc in psutil.process_iter():
    if proc.name() == 'caffeine.exe':
      return
  # Extract and run
  extract_item('Caffeine', silent=True)
  try:
    popen_program([global_vars['Tools']['Caffeine']])
  except Exception:
    print_error('ERROR: No caffeine available.')
    print_warning('Please set the power setting to High Performance.')


def wait_for_process(name, poll_rate=3):
  """Wait for process by name."""
  running = True
  while running:
    sleep(poll_rate)
    running = False
    for proc in psutil.process_iter():
      try:
        if re.search(r'^{}'.format(name), proc.name(), re.IGNORECASE):
          running = True
      except psutil._exceptions.NoSuchProcess:
        # Assuming process closed during iteration
        pass
  sleep(1)


# global_vars functions
def init_global_vars(silent=False):
  """Sets global variables based on system info."""
  if not silent:
    print_info('Initializing')
  if psutil.WINDOWS:
    os.system('title Wizard Kit')
  if psutil.LINUX:
    init_functions = [
      ['Checking environment...', set_linux_vars],
      ['Clearing collisions...',  clean_env_vars],
      ]
  else:
    init_functions = [
      ['Checking .bin...',    find_bin],
      ['Checking environment...', set_common_vars],
      ['Checking OS...',      check_os],
      ['Checking tools...',     check_tools],
      ['Creating folders...',   make_tmp_dirs],
      ['Clearing collisions...',  clean_env_vars],
      ]
  try:
    if silent:
      for f in init_functions:
        f[1]()
    else:
      for f in init_functions:
        try_and_print(
          message=f[0], function=f[1],
          cs='Done', ns='Error', catch_all=False)
  except:
    major_exception()


def check_os():
  """Set OS specific variables."""
  tmp = {}

  # Query registry
  path = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'
  with winreg.OpenKey(HKLM, path) as key:
    for name in ['CurrentBuild', 'CurrentVersion', 'ProductName']:
      try:
        tmp[name] = winreg.QueryValueEx(key, name)[0]
      except FileNotFoundError:
        tmp[name] = 'Unknown'

  # Handle CurrentBuild collision
  if tmp['CurrentBuild'] == '9200':
    if tmp['CurrentVersion'] == '6.2':
      # Windown 8, set to fake build number
      tmp['CurrentBuild'] = '9199'
    else:
      # Windows 8.1, leave alone
      pass

  # Check bit depth
  tmp['Arch'] = 32
  if 'PROGRAMFILES(X86)' in global_vars['Env']:
    tmp['Arch'] = 64

  # Get Windows build info
  build_info = WINDOWS_BUILDS.get(tmp['CurrentBuild'], None)
  if build_info is None:
    # Not in windows_builds.py
    build_info = [
      'Unknown',
      'Build {}'.format(tmp['CurrentBuild']),
      None,
      None,
      'unrecognized']
  else:
    build_info = list(build_info)
  tmp['Version'] = build_info.pop(0)
  tmp['Release'] = build_info.pop(0)
  tmp['Codename'] = build_info.pop(0)
  tmp['Marketing Name'] = build_info.pop(0)
  tmp['Notes'] = build_info.pop(0)

  # Set name
  tmp['Name'] = tmp['ProductName']
  if tmp['Release']:
    tmp['Name'] += ' {}'.format(tmp['Release'])
  if tmp['Codename']:
    tmp['Name'] += ' "{}"'.format(tmp['Codename'])
  if tmp['Marketing Name']:
    tmp['Name'] += ' / "{}"'.format(tmp['Marketing Name'])
  tmp['Name'] = re.sub(r'\s+', ' ', tmp['Name'])

  # Set display name
  tmp['DisplayName'] = '{} x{}'.format(tmp['Name'], tmp['Arch'])
  if tmp['Notes']:
    tmp['DisplayName'] += ' ({})'.format(tmp['Notes'])

  global_vars['OS'] = tmp


def check_tools():
  """Set tool variables based on OS bit-depth and tool availability."""
  if global_vars['OS'].get('Arch', 32) == 64:
    global_vars['Tools'] = {
      k: v.get('64', v.get('32')) for (k, v) in TOOLS.items()}
  else:
    global_vars['Tools'] = {k: v.get('32') for (k, v) in TOOLS.items()}

  # Fix paths
  global_vars['Tools'] = {k: os.path.join(global_vars['BinDir'], v)
    for (k, v) in global_vars['Tools'].items()}


def clean_env_vars():
  """Remove conflicting global_vars and env variables.

  This fixes an issue where both global_vars and
  global_vars['Env'] are expanded at the same time."""
  for key in global_vars.keys():
    global_vars['Env'].pop(key, None)


def find_bin():
  """Find .bin folder in the cwd or it's parents."""
  wd = os.getcwd()
  base = None
  while base is None:
    if os.path.exists('.bin'):
      base = os.getcwd()
      break
    if re.fullmatch(r'\w:\\', os.getcwd()):
      break
    os.chdir('..')
  os.chdir(wd)
  if base is None:
    raise BinNotFoundError
  global_vars['BaseDir'] = base


def generate_global_vars_report():
  """Build readable string from global_vars, returns str."""
  report = ['global_vars: {']
  for k, v in sorted(global_vars.items()):
    if k == 'Env':
      continue
    if isinstance(v, list):
      report.append('  {}: ['.format(str(k)))
      for item in v:
        report.append('    {}'.format(str(v)))
      report.append('  ]')
    elif isinstance(v, dict):
      report.append('  {}: {{'.format(str(k)))
      for item_k, item_v in sorted(v.items()):
        report.append('    {:<15} {}'.format(
          str(item_k)+':', str(item_v)))
      report.append('  }')
    else:
      report.append('  {:<18}{}'.format(str(k)+':', str(v)))
  report.append('  Env:')
  for k, v in sorted(global_vars.get('Env', {}).items()):
    report.append('    {:<15} {}'.format(
      str(k)+':', str(v)))
  report.append('}')

  return '\n'.join(report)


def make_tmp_dirs():
  """Make temp directories."""
  os.makedirs(global_vars['BackupDir'], exist_ok=True)
  os.makedirs(global_vars['LogDir'], exist_ok=True)
  os.makedirs(r'{}\{}'.format(
    global_vars['LogDir'], KIT_NAME_FULL), exist_ok=True)
  os.makedirs(r'{}\Tools'.format(global_vars['LogDir']), exist_ok=True)
  os.makedirs(global_vars['TmpDir'], exist_ok=True)


def set_common_vars():
  """Set common variables."""
  global_vars['Date'] =             time.strftime("%Y-%m-%d")
  global_vars['Date-Time'] =        time.strftime("%Y-%m-%d_%H%M_%z")
  global_vars['Env'] =              os.environ.copy()

  global_vars['ArchivePassword'] =  ARCHIVE_PASSWORD
  global_vars['BinDir'] =           r'{BaseDir}\.bin'.format(**global_vars)
  global_vars['CBinDir'] =          r'{BaseDir}\.cbin'.format(**global_vars)
  global_vars['ClientDir'] =        r'{SYSTEMDRIVE}\{prefix}'.format(
                                      prefix=KIT_NAME_SHORT, **global_vars['Env'])
  global_vars['BackupDir'] =        r'{ClientDir}\Backups'.format(**global_vars)
  global_vars['LogDir'] =           r'{ClientDir}\Logs\{Date}'.format(**global_vars)
  global_vars['QuarantineDir'] =    r'{ClientDir}\Quarantine'.format(**global_vars)
  global_vars['TmpDir'] =           r'{BinDir}\tmp'.format(**global_vars)


def set_linux_vars():
  """Set common variables in a Linux environment.

  These assume we're running under a WK-Linux build."""
  result = run_program(['mktemp', '-d'])
  global_vars['TmpDir'] =           result.stdout.decode().strip()
  global_vars['Date'] =             time.strftime("%Y-%m-%d")
  global_vars['Date-Time'] =        time.strftime("%Y-%m-%d_%H%M_%z")
  global_vars['Env'] =              os.environ.copy()
  global_vars['BinDir'] =           '/usr/local/bin'
  global_vars['LogDir'] =           '{}/Logs'.format(global_vars['Env']['HOME'])
  global_vars['Tools'] = {
    'wimlib-imagex': 'wimlib-imagex',
    'SevenZip': '7z',
    }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
