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
  'RED':  '\033[31m',
  'ORANGE': '\033[31;1m',
  'GREEN':  '\033[32m',
  'YELLOW': '\033[33m',
  'BLUE':   '\033[34m',
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

class NotInstalledError(Exception):
  pass

class NoProfilesError(Exception):
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


# General functions
def abort():
  """Abort script."""
  print_warning('Aborted.')
  sleep(1)
  pause(prompt='Press Enter to exit... ')
  exit_script()


def ask(prompt='Kotaero!'):
  """Prompt the user with a Y/N question, returns bool."""
  answer = None
  prompt = '{} [Y/N]: '.format(prompt)
  while answer is None:
    tmp = input(prompt)
    if re.search(r'^y(es|)$', tmp, re.IGNORECASE):
      answer = True
    elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
      answer = False
  message = '{prompt}{answer_text}'.format(
    prompt = prompt,
    answer_text = 'Yes' if answer else 'No')
  print_log(message=message)
  return answer


def choice(choices, prompt='Kotaero!'):
  """Prompt the user with a choice question, returns str."""
  answer = None
  choices = [str(c) for c in choices]
  choices_short = {c[:1].upper(): c for c in choices}
  prompt = '{} [{}]: '.format(prompt, '/'.join(choices))
  regex = '^({}|{})$'.format(
    '|'.join([c[:1] for c in choices]),
    '|'.join(choices))

  # Get user's choice
  while answer is None:
    tmp = input(prompt)
    if re.search(regex, tmp, re.IGNORECASE):
      answer = tmp

  # Log result
  message = '{prompt}{answer_text}'.format(
    prompt = prompt,
    answer_text = 'Yes' if answer else 'No')
  print_log(message=message)

  # Fix answer formatting to match provided values
  answer = choices_short[answer[:1].upper()]

  # Done
  return answer


def clear_screen():
  """Simple wrapper for cls/clear."""
  if psutil.WINDOWS:
    os.system('cls')
  else:
    os.system('clear')


def convert_to_bytes(size):
  """Convert human-readable size str to bytes and return an int."""
  size = str(size)
  tmp = re.search(r'(\d+\.?\d*)\s+([KMGT]B)', size.upper())
  if tmp:
    size = float(tmp.group(1))
    units = tmp.group(2)
    if units == 'TB':
      size *= 1099511627776
    elif units == 'GB':
      size *= 1073741824
    elif units == 'MB':
      size *= 1048576
    elif units == 'KB':
      size *= 1024
    size = int(size)
  else:
    return -1

  return size


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


def get_simple_string(prompt='Enter string'):
  """Get string from user (restricted character set), returns str."""
  simple_string = None
  while simple_string is None:
    _input = input('{}: '.format(prompt))
    if re.match(r"^(\w|-| |\.|')+$", _input, re.ASCII):
      simple_string = _input.strip()
  return simple_string


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


def human_readable_size(size, decimals=0):
  """Convert size from bytes to a human-readable format, returns str."""
  # Prep string formatting
  width = 3+decimals
  if decimals > 0:
    width += 1

  # Convert size to int
  try:
    size = int(size)
  except ValueError:
    size = convert_to_bytes(size)
  except TypeError:
    size = -1

  # Verify we have a valid size
  if size < 0:
    return '{size:>{width}} b'.format(size='???', width=width)

  # Convert to sensible units
  if size >= 1099511627776:
    size /= 1099511627776
    units = 'Tb'
  elif size >= 1073741824:
    size /= 1073741824
    units = 'Gb'
  elif size >= 1048576:
    size /= 1048576
    units = 'Mb'
  elif size >= 1024:
    size /= 1024
    units = 'Kb'
  else:
    units = ' b'

  # Return
  return '{size:>{width}.{decimals}f} {units}'.format(
    size=size, width=width, decimals=decimals, units=units)


def kill_process(name):
  """Kill any running caffeine.exe processes."""
  for proc in psutil.process_iter():
    if proc.name() == name:
      proc.kill()


def major_exception():
  """Display traceback and exit"""
  print_error('Major exception')
  print_warning(SUPPORT_MESSAGE)
  print(traceback.format_exc())
  print_log(traceback.format_exc())
  try:
    upload_crash_details()
  except GenericAbort:
    # User declined upload
    print_warning('Upload: Aborted')
    sleep(10)
  except GenericError:
    # No log file or uploading disabled
    sleep(10)
  except:
    print_error('Upload: NS')
    sleep(10)
  else:
    print_success('Upload: CS')
  pause('Press Enter to exit...')
  exit_script(1)


def menu_select(
    title='[Untitled Menu]',
    prompt='Please make a selection', secret_actions=[], secret_exit=False,
    main_entries=[], action_entries=[], disabled_label='DISABLED',
    spacer=''):
  """Display options in a menu and return selected option as a str."""
  # Bail early
  if not main_entries and not action_entries:
    raise Exception("MenuError: No items given")

  # Set title
  if 'Title' in global_vars:
    title = '{}\n\n{}'.format(global_vars['Title'], title)

  # Build menu
  menu_splash = '{}\n{}\n'.format(title, spacer)
  width = len(str(len(main_entries)))
  valid_answers = []
  if secret_exit:
    valid_answers.append('Q')
  if secret_actions:
    valid_answers.extend(secret_actions)

  # Add main entries
  for i in range(len(main_entries)):
    entry = main_entries[i]
    # Add Spacer
    if ('CRLF' in entry):
      menu_splash += '{}\n'.format(spacer)
    entry_str = '{number:>{width}}: {name}'.format(
        number =  i+1,
        width =   width,
        name =    entry.get('Display Name', entry['Name']))
    if entry.get('Disabled', False):
      entry_str = '{YELLOW}{entry_str} ({disabled}){CLEAR}'.format(
        entry_str = entry_str,
        disabled =  disabled_label,
        **COLORS)
    else:
      valid_answers.append(str(i+1))
    menu_splash += '{}\n'.format(entry_str)
  menu_splash += '{}\n'.format(spacer)

  # Add action entries
  for entry in action_entries:
    # Add Spacer
    if ('CRLF' in entry):
      menu_splash += '{}\n'.format(spacer)
    valid_answers.append(entry['Letter'])
    menu_splash += '{letter:>{width}}: {name}\n'.format(
      letter =  entry['Letter'].upper(),
      width =   len(str(len(action_entries))),
      name =    entry['Name'])

  answer = ''

  while (answer.upper() not in valid_answers):
    clear_screen()
    print(menu_splash)
    answer = input('{}: '.format(prompt))

  return answer.upper()


def non_clobber_rename(full_path):
  """Append suffix to path, if necessary, to avoid clobbering path"""
  new_path = full_path
  _i = 1;
  while os.path.exists(new_path):
    new_path = '{path}_{i}'.format(i=_i, path=full_path)
    _i += 1

  return new_path


def pause(prompt='Press Enter to continue... '):
  """Simple pause implementation."""
  input(prompt)


def ping(addr='google.com'):
  """Attempt to ping addr."""
  cmd = [
    'ping',
    '-n' if psutil.WINDOWS else '-c',
    '2',
    addr]
  run_program(cmd)


def popen_program(cmd, pipe=False, minimized=False, shell=False, **kwargs):
  """Run program and return a subprocess.Popen object."""
  cmd_kwargs = {'args': cmd, 'shell': shell}

  if minimized:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 6
    cmd_kwargs['startupinfo'] = startupinfo

  if pipe:
    cmd_kwargs.update({
      'stdout': subprocess.PIPE,
      'stderr': subprocess.PIPE,
      })

  if 'cwd' in kwargs:
    cmd_kwargs['cwd'] = kwargs['cwd']

  return subprocess.Popen(**cmd_kwargs)


def print_error(*args, **kwargs):
  """Prints message to screen in RED."""
  print_standard(*args, color=COLORS['RED'], **kwargs)


def print_info(*args, **kwargs):
  """Prints message to screen in BLUE."""
  print_standard(*args, color=COLORS['BLUE'], **kwargs)


def print_standard(message='Generic info',
  color=None, end='\n', timestamp=True, **kwargs):
  """Prints message to screen and log (if set)."""
  display_message = message
  if color:
    display_message = color + message + COLORS['CLEAR']
  # **COLORS is used below to support non-"standard" color printing
  print(display_message.format(**COLORS), end=end, **kwargs)
  print_log(message, end, timestamp)


def print_success(*args, **kwargs):
  """Prints message to screen in GREEN."""
  print_standard(*args, color=COLORS['GREEN'], **kwargs)


def print_warning(*args, **kwargs):
  """Prints message to screen in YELLOW."""
  print_standard(*args, color=COLORS['YELLOW'], **kwargs)


def print_log(message='', end='\n', timestamp=True):
  """Writes message to a log if LogFile is set."""
  time_str = time.strftime("%Y-%m-%d %H%M%z: ") if timestamp else ''
  if 'LogFile' in global_vars and global_vars['LogFile']:
    with open(global_vars['LogFile'], 'a', encoding='utf-8') as f:
      for line in message.splitlines():
        f.write('{timestamp}{line}{end}'.format(
          timestamp = time_str,
          line =    line,
          end =     end))


def run_program(cmd, args=[], check=True, pipe=True, shell=False, **kwargs):
  """Run program and return a subprocess.CompletedProcess object."""
  if args:
    # Deprecated so let's raise an exception to find & fix all occurances
    print_error('ERROR: Using args is no longer supported.')
    raise Exception
  cmd = [c for c in cmd if c]
  if shell:
    cmd = ' '.join(cmd)

  cmd_kwargs = {'args': cmd, 'check': check, 'shell': shell}

  if pipe:
    cmd_kwargs.update({
      'stdout': subprocess.PIPE,
      'stderr': subprocess.PIPE,
      })

  if 'cwd' in kwargs:
    cmd_kwargs['cwd'] = kwargs['cwd']

  return subprocess.run(**cmd_kwargs)


def set_title(title='[Some Title]'):
  """Set title.

  Used for window title and menu titles."""
  global_vars['Title'] = title
  os.system('title {}'.format(title))


def show_data(
    message='[Some message]', data='[Some data]',
    indent=8, width=32,
    info=False, warning=False, error=False):
  """Display info with formatting."""
  message = '{indent}{message:<{width}}{data}'.format(
    indent=' '*indent, width=width, message=message, data=data)
  if error:
    print_error(message)
  elif warning:
    print_warning(message)
  elif info:
    print_info(message)
  else:
    print_standard(message)


def sleep(seconds=2):
  """Wait for a while."""
  time.sleep(seconds)


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


def strip_colors(s):
  """Remove all ASCII color escapes from string, returns str."""
  for c in COLORS.values():
    s = s.replace(c, '')
  return s


def get_exception(s):
  """Get exception by name, returns Exception object."""
  try:
    obj = getattr(sys.modules[__name__], s)
  except AttributeError:
    # Try builtin classes
    obj = getattr(sys.modules['builtins'], s)
  return obj


def try_and_print(message='Trying...',
  function=None, cs='CS', ns='NS', other_results={},
  catch_all=True, print_return=False, silent_function=True,
  indent=8, width=32, *args, **kwargs):
  """Run function, print if successful or not, and return dict.

  other_results is in the form of
    {
      'Warning': {'ExceptionClassName': 'Result Message'},
      'Error':   {'ExceptionClassName': 'Result Message'}
      }
    The the ExceptionClassNames will be excepted conditions
    and the result string will be printed in the correct color.
  catch_all=False will re-raise unspecified exceptions."""
  err = None
  out = None
  w_exceptions = other_results.get('Warning', {}).keys()
  w_exceptions = tuple(get_exception(e) for e in w_exceptions)
  e_exceptions = other_results.get('Error', {}).keys()
  e_exceptions = tuple(get_exception(e) for e in e_exceptions)
  w_results = other_results.get('Warning', {})
  e_results = other_results.get('Error', {})

  # Run function and catch errors
  print_standard('{indent}{message:<{width}}'.format(
    indent=' '*indent, message=message, width=width), end='', flush=True)
  try:
    out = function(*args, **kwargs)
    if print_return:
      str_list = out
      if isinstance(out, subprocess.CompletedProcess):
        str_list = out.stdout.decode().strip().splitlines()
      print_standard(str_list[0].strip(), timestamp=False)
      for item in str_list[1:]:
        print_standard('{indent}{item}'.format(
          indent=' '*(indent+width), item=item.strip()))
    elif silent_function:
      print_success(cs, timestamp=False)
  except w_exceptions as e:
    _result = w_results.get(e.__class__.__name__, 'Warning')
    print_warning(_result, timestamp=False)
    err = e
  except e_exceptions as e:
    _result = e_results.get(e.__class__.__name__, 'Error')
    print_error(_result, timestamp=False)
    err = e
  except Exception:
    print_error(ns, timestamp=False)
    err = traceback.format_exc()

  # Return or raise?
  if err and not catch_all:
    raise
  else:
    return {'CS': not bool(err), 'Error': err, 'Out': out}


def upload_crash_details():
  """Upload log and runtime data to the CRASH_SERVER.

  Intended for uploading to a public Nextcloud share."""
  if not ENABLED_UPLOAD_DATA:
    raise GenericError

  import requests
  if 'LogFile' in global_vars and global_vars['LogFile']:
    if ask('Upload crash details to {}?'.format(CRASH_SERVER['Name'])):
      with open(global_vars['LogFile']) as f:
        data = '{}\n'.format(f.read())
        data += '#############################\n'
        data += 'Runtime Details:\n\n'
        data += 'sys.argv: {}\n\n'.format(sys.argv)
        data += 'global_vars: {}\n'.format(global_vars)
        filename = global_vars.get('LogFile', 'Unknown')
        filename = re.sub(r'.*(\\|/)', '', filename)
        filename += '.txt'
        url = '{}/Crash_{}__{}'.format(
          CRASH_SERVER['Url'],
          global_vars.get('Date-Time', 'Unknown Date-Time'),
          filename)
        r = requests.put(
          url, data=data,
          headers={'X-Requested-With': 'XMLHttpRequest'},
          auth=(CRASH_SERVER['User'], CRASH_SERVER['Pass']))
        # Raise exception if upload NS
        if not r.ok:
          raise Exception
    else:
      # User said no
      raise GenericAbort
  else:
    # No LogFile defined (or invalid LogFile)
    raise GenericError


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
  global_vars['Date'] =         time.strftime("%Y-%m-%d")
  global_vars['Date-Time'] =      time.strftime("%Y-%m-%d_%H%M_%z")
  global_vars['Env'] =        os.environ.copy()

  global_vars['ArchivePassword'] =  ARCHIVE_PASSWORD
  global_vars['BinDir'] =       r'{BaseDir}\.bin'.format(
    **global_vars)
  global_vars['CBinDir'] =      r'{BaseDir}\.cbin'.format(
    **global_vars)
  global_vars['ClientDir'] =      r'{SYSTEMDRIVE}\{prefix}'.format(
    prefix=KIT_NAME_SHORT, **global_vars['Env'])
  global_vars['BackupDir'] =      r'{ClientDir}\Backups'.format(
    **global_vars)
  global_vars['LogDir'] =       r'{ClientDir}\Logs\{Date}'.format(
    **global_vars)
  global_vars['QuarantineDir'] =    r'{ClientDir}\Quarantine'.format(
    **global_vars)
  global_vars['TmpDir'] =       r'{BinDir}\tmp'.format(
    **global_vars)


def set_linux_vars():
  """Set common variables in a Linux environment.

  These assume we're running under a WK-Linux build."""
  result = run_program(['mktemp', '-d'])
  global_vars['TmpDir'] =       result.stdout.decode().strip()
  global_vars['Date'] =         time.strftime("%Y-%m-%d")
  global_vars['Date-Time'] =      time.strftime("%Y-%m-%d_%H%M_%z")
  global_vars['Env'] =        os.environ.copy()
  global_vars['BinDir'] =       '/usr/local/bin'
  global_vars['LogDir'] =       global_vars['TmpDir']
  global_vars['Tools'] = {
    'wimlib-imagex': 'wimlib-imagex',
    'SevenZip': '7z',
    }


def set_log_file(log_name):
  """Sets global var LogFile and creates path as needed."""
  folder_path = r'{}\{}'.format(global_vars['LogDir'], KIT_NAME_FULL)
  log_file = r'{}\{}'.format(folder_path, log_name)
  os.makedirs(folder_path, exist_ok=True)
  global_vars['LogFile'] = log_file


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
