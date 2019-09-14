'''WizardKit: Standard Functions'''
# vim: sts=2 sw=2 ts=2

import itertools
import logging
import lzma
import os
import pathlib
import platform
import re
import subprocess
import sys
import time
import traceback

from collections import OrderedDict
try:
  from termios import tcflush, TCIOFLUSH
except ImportError:
  if os.name == 'posix':
    # Not worried about this under Windows
    raise

from wk.cfg.main import (
  CRASH_SERVER,
  ENABLED_UPLOAD_DATA,
  INDENT,
  SUPPORT_MESSAGE,
  WIDTH,
  )


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
LOG = logging.getLogger(__name__)
REGEX_SIZE_STRING = re.compile(
  r'(?P<size>\-?\d+\.?\d*)\s*(?P<units>[PTGMKB])(?P<binary>I?)B?'
  )


# Exception Classes
class GenericAbort(Exception):
  """Exception used for aborts selected by the user at runtime."""

class GenericError(Exception):
  """Exception used when the built-in exceptions don't fit."""

class GenericWarning(Exception):
  """Exception used to highlight non-critical events.

  NOTE: Avoiding built-in warning exceptions in case the
        warnings filter has been changed from the default.
  """


# Classes
class Menu():
  """Object for tracking menu specific data and methods.

  Menu items are added to an OrderedDict so the order is preserved.

  ASSUMPTIONS:
  1. All entry names are unique.
  2. All action entry names start with different letters.
  """
  def __init__(self, title='[Untitled Menu]'):
    self.actions = OrderedDict()
    self.options = OrderedDict()
    self.sets = OrderedDict()
    self.toggles = OrderedDict()
    self.disabled_str = 'Disabled'
    self.separator = '─'
    self.title = title

  def _generate_menu_text(self):
    """Generate menu text, returns str."""
    separator_string = self._get_separator_string()
    menu_lines = [self.title, separator_string]

    # Sets & toggles
    for section in (self.sets, self.toggles):
      for details in section.values():
        if details.get('Hidden', False):
          continue
        if details.get('Separator', False):
          menu_lines.append(separator_string)
        menu_lines.append(details['Display Name'])
    if self.sets or self.toggles:
      menu_lines.append(separator_string)

    # Options
    for details in self.options.values():
      if details.get('Hidden', False):
        continue
      if details.get('Separator', False):
        menu_lines.append(separator_string)
      menu_lines.append(details['Display Name'])
    if self.options:
      menu_lines.append(separator_string)

    # Actions
    for details in self.actions.values():
      if details.get('Hidden', False):
        continue
      if details.get('Separator', False):
        menu_lines.append(separator_string)
      menu_lines.append(details['Display Name'])

    # Show menu
    menu_lines.append('')
    menu_lines = [str(line) for line in menu_lines]
    return '\n'.join(menu_lines)

  def _get_display_name(self, name, details, index=None, no_checkboxes=True):
    # pylint: disable=no-self-use
    """Format display name based on details and args, returns str."""
    disabled = details.get('Disabled', False)
    checkmark = '*'
    if 'DISPLAY' in os.environ or sys.platform == 'darwin':
      checkmark = '✓'
    clear_code = COLORS['CLEAR']
    color_code = COLORS['YELLOW'] if disabled else ''
    display_name = f'{color_code}{index if index else name[:1].upper()}: '
    if not (index and index >= 10):
      display_name = f' {display_name}'

    # Add enabled status if necessary
    if not no_checkboxes:
      display_name += f'[{checkmark if details["Selected"] else " "}] '

    # Add name
    if disabled:
      display_name += f'{name} ({self.disabled_str}){clear_code}'
    else:
      display_name += name

    # Done
    return display_name

  def _get_separator_string(self):
    """Format separator length based on name lengths, returns str."""
    separator_length = 0

    # Check title line(s)
    for line in self.title.split('\n'):
      separator_length = max(separator_length, len(strip_colors(line)))

    # Loop over all item names
    for section in (self.actions, self.options, self.sets, self.toggles):
      for details in section.values():
        if details.get('Hidden', False):
          # Skip hidden lines
          continue
        line = strip_colors(details['Display Name'])
        separator_length = max(separator_length, len(line))
    separator_length += 1

    # Done
    return self.separator * separator_length

  def _get_valid_answers(self):
    """Get valid answers based on menu items, returns list."""
    valid_answers = []

    # Numbered items
    index = 0
    for section in (self.sets, self.toggles, self.options):
      for details in section.values():
        if details.get('Hidden', False):
          # Don't increment index or add to valid_answers
          continue
        index += 1
        if not details.get('Disabled', False):
          valid_answers.append(str(index))

    # Action items
    for name, details in self.actions.items():
      if not details.get('Disabled', False):
        valid_answers.append(name[:1].upper())

    # Done
    return valid_answers

  def _resolve_selection(self, selection):
    """Get menu item based on user selection, returns tuple."""
    offset = 1
    resolved_selection = None
    if selection.isnumeric():
      # Enumerate over numbered entries
      entries = [
        *self.sets.items(),
        *self.toggles.items(),
        *self.options.items(),
        ]
      for _i, details in enumerate(entries):
        if details[1].get('Hidden', False):
          offset -= 1
        elif str(_i+offset) == selection:
          resolved_selection = (details)
          break
    else:
      # Just check actions
      for action, details in self.actions.items():
        if action.lower().startswith(selection.lower()):
          resolved_selection = (action, details)
          break

    # Done
    return resolved_selection

  def _update(self, single_selection=True):
    """Update menu items in preparation for printing to screen."""
    index = 0

    # Fix selection status for sets
    for set_details in self.sets.values():
      set_selected = True
      set_targets = set_details['Targets']
      for option, option_details in self.options.items():
        if option in set_targets and not option_details['Selected']:
          set_selected = False
        elif option not in set_targets and option_details['Selected']:
          set_selected = False
      set_details['Selected'] = set_selected

    # Numbered sections
    for section in (self.sets, self.toggles, self.options):
      for name, details in section.items():
        if details.get('Hidden', False):
          # Skip hidden lines and don't increment index
          continue
        index += 1
        details['Display Name'] = self._get_display_name(
          name,
          details,
          index=index,
          no_checkboxes=single_selection,
          )

    # Actions
    for name, details in self.actions.items():
      details['Display Name'] = self._get_display_name(
        name,
        details,
        no_checkboxes=True,
        )

  def _update_entry_selection_status(self, entry, toggle=True, status=None):
    """Update entry selection status either directly or by toggling."""
    if entry in self.sets:
      # Update targets not the set itself
      new_status = not self.sets[entry]['Selected'] if toggle else status
      targets = self.sets[entry]['Targets']
      self._update_set_selection_status(targets, new_status)
    for section in (self.toggles, self.options, self.actions):
      if entry in section:
        if toggle:
          section[entry]['Selected'] = not section[entry]['Selected']
        else:
          section[entry]['Selected'] = status

  def _update_set_selection_status(self, targets, status):
    """Select or deselect options based on targets and status."""
    for option, details in self.options.items():
      # If (new) status is True and this option is a target then select
      #   Otherwise deselect
      details['Selected'] = status and option in targets

  def _user_select(self, prompt):
    """Show menu and select an entry, returns str."""
    menu_text = self._generate_menu_text()
    valid_answers = self._get_valid_answers()

    # Menu loop
    while True:
      clear_screen()
      print(menu_text)
      sleep(0.01)
      answer = input_text(prompt).strip()
      if answer.upper() in valid_answers:
        break

    # Done
    return answer

  def add_action(self, name, details=None):
    """Add action to menu."""
    details = details if details else {}
    details['Selected'] = details.get('Selected', False)
    self.actions[name] = details

  def add_option(self, name, details=None):
    """Add option to menu."""
    details = details if details else {}
    details['Selected'] = details.get('Selected', False)
    self.options[name] = details

  def add_set(self, name, details=None):
    """Add set to menu."""
    details = details if details else {}
    details['Selected'] = details.get('Selected', False)

    # Safety check
    if 'Targets' not in details:
      raise KeyError('Menu set has no targets')

    # Add set
    self.sets[name] = details

  def add_toggle(self, name, details=None):
    """Add toggle to menu."""
    details = details if details else {}
    details['Selected'] = details.get('Selected', False)
    self.toggles[name] = details

  def advanced_select(self, prompt='Please make a selection: '):
    """Display menu and make multiple selections, returns tuple.

    NOTE: Menu is displayed until an action entry is selected.
    """
    while True:
      self._update(single_selection=False)
      user_selection = self._user_select(prompt)
      selected_entry = self._resolve_selection(user_selection)
      if user_selection.isnumeric():
        # Update selection(s)
        self._update_entry_selection_status(selected_entry[0])
      else:
        # Action selected
        break

    # Done
    return selected_entry

  def simple_select(self, prompt='Please make a selection: '):
    """Display menu and make a single selection, returns tuple."""
    self._update()
    user_selection = self._user_select(prompt)
    return self._resolve_selection(user_selection)


class TryAndPrint():
  """Object used to standardize running functions and returning the result.

  The errors and warning attributes are used to allow fine-tuned results
  based on exception names.
  """
  def __init__(self, msg_bad='FAILED', msg_good='SUCCESS'):
    self.indent = INDENT
    self.msg_bad = msg_bad
    self.msg_good = msg_good
    self.width = WIDTH
    self.list_errors = ['GenericError']
    self.list_warnings = ['GenericWarning']

  def _format_exception_message(self, _exception):
    """Format using the exception's args or name, returns str."""
    # pylint: disable=broad-except
    LOG.debug(
      'Formatting exception: %s',
      _exception.__class__.__name__,
      )
    message = None

    # Use known argument index or first string found
    try:
      if isinstance(_exception, subprocess.CalledProcessError):
        message = _exception.stderr
        if not isinstance(message, str):
          message = message.decode('utf-8')
        message = message.strip()
      elif isinstance(_exception, FileNotFoundError):
        message = _exception.args[1]
      elif isinstance(_exception, ZeroDivisionError):
        message = 'ZeroDivisionError'
      else:
        for arg in _exception.args:
          if isinstance(arg, str):
            message = arg
            break
    except Exception:
      # Just use the exception name instead
      pass

    # Safety check
    if not message:
      try:
        message = _exception.__class__.__name__
      except Exception:
        message = 'UNKNOWN ERROR'

    # Fix multi-line messages
    if '\n' in message:
      try:
        lines = [
          f'{" "*(self.indent+self.width)}{line.strip()}'
          for line in message.splitlines() if line.strip()
          ]
        lines[0] = lines[0].strip()
        message = '\n'.join(lines)
      except Exception:
        pass

    # Done
    return message

  def _format_function_output(self, output):
    """Format function output for use in try_and_print(), returns str."""
    LOG.debug('Formatting output: %s', output)

    if not output:
      raise GenericWarning('No output')

    # Ensure we're working with a list
    if isinstance(output, subprocess.CompletedProcess):
      stdout = output.stdout
      if not isinstance(stdout, str):
        stdout = stdout.decode('utf8')
      output = stdout.strip().splitlines()
    else:
      output = list(output)

    # Safety check
    if not output:
      # Going to ignore empty function output for now
      LOG.error('Output is empty')
      return 'UNKNOWN'

    # Build result_msg
    result_msg = f'{output.pop(0)}'
    if output:
      output = [f'{" "*(self.indent+self.width)}{line}' for line in output]
      result_msg += '\n' + '\n'.join(output)

    # Done
    return result_msg

  def _get_exception(self, name):
    # pylint: disable=no-self-use
    """Get exception by name, returns exception object.

    [Doctest]
    >>> self._get_exception('AttributeError')
    <class 'AttributeError'>
    >>> self._get_exception('CalledProcessError')
    <class 'subprocess.CalledProcessError'>
    >>> self._get_exception('GenericError')
    <class 'std.GenericError'>
    """
    LOG.debug('Getting exception: %s', name)
    try:
      obj = getattr(sys.modules[__name__], name)
    except AttributeError:
      # Try builtin classes
      obj = getattr(sys.modules['builtins'], name)
    return obj

  def add_error(self, exception_name):
    """Add exception name to error list."""
    if exception_name not in self.list_errors:
      self.list_errors.append(exception_name)

  def add_warning(self, exception_name):
    """Add exception name to warning list."""
    if exception_name not in self.list_warnings:
      self.list_warnings.append(exception_name)

  def run_function(
      self, message, function, *args,
      catch_all=True, print_return=False, verbose=False, **kwargs):
    # pylint: disable=catching-non-exception
    """Run a function and print the results, returns results as dict.

    If catch_all is True then (nearly) all exceptions will be caught.
    Otherwise if an exception occurs that wasn't specified it will be
    re-raised.

    If print_return is True then the output from the function will be used
    instead of msg_good, msg_bad, or exception text. The output should be
    a list or a subprocess.CompletedProcess object.

    If verbose is True then exception names or messages will be used for
    the result message. Otherwise it will simply be set to result_bad.

    args and kwargs are passed to the function.
    """
    LOG.debug('function: %s.%s', function.__module__, function.__name__)
    LOG.debug('args: %s', args)
    LOG.debug('kwargs: %s', kwargs)
    LOG.debug(
      'catch_all: %s, print_return: %s, verbose: %s',
      catch_all,
      print_return,
      verbose,
      )
    f_exception = None
    output = None
    result_msg = 'UNKNOWN'

    # Build exception tuples
    e_exceptions = tuple(self._get_exception(e) for e in self.list_errors)
    w_exceptions = tuple(self._get_exception(e) for e in self.list_warnings)

    # Run function and catch exceptions
    print(f'{" "*self.indent}{message:<{self.width}}', end='', flush=True)
    LOG.info('Running function: %s.%s', function.__module__, function.__name__)
    try:
      output = function(*args, **kwargs)
      if print_return:
        result_msg = self._format_function_output(output)
        print(result_msg)
      else:
        print_success(self.msg_good)
    except w_exceptions as _exception:
      result_msg = self._format_exception_message(_exception)
      print_warning(result_msg)
      f_exception = _exception
    except e_exceptions as _exception:
      result_msg = self._format_exception_message(_exception)
      print_error(result_msg)
      f_exception = _exception
    except Exception as _exception: # pylint: disable=broad-except
      if verbose:
        result_msg = self._format_exception_message(_exception)
      else:
        result_msg = self.msg_bad
      print_error(result_msg)
      f_exception = _exception
      if not catch_all:
        # Re-raise error as necessary
        raise

    # Done
    LOG.info('Result: %s', result_msg.strip())
    return {
      'Failed': bool(f_exception),
      'Exception': f_exception,
      'Output': output,
      }


# Functions
def abort(prompt='Aborted.', show_prompt=True, return_code=1):
  """Abort script."""
  print_warning(prompt)
  LOG.warning(prompt)
  if show_prompt:
    sleep(1)
    pause(prompt='Press Enter to exit... ')
  sys.exit(return_code)


def ask(prompt='Kotaero!'):
  """Prompt the user with a Y/N question, returns bool."""
  answer = None
  prompt = f'{prompt} [Y/N]: '

  # Loop until acceptable answer is given
  while answer is None:
    tmp = input_text(prompt)
    if re.search(r'^y(es|up|)$', tmp, re.IGNORECASE):
      answer = True
    elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
      answer = False

  # Done
  LOG.info('%s%s', prompt, 'Yes' if answer else 'No')
  return answer


def beep(repeat=1):
  """Play system bell with optional repeat."""
  # TODO: Verify Windows functionality
  while repeat >= 1:
    # Print bell char without a newline
    print('\a', end='', flush=True)
    sleep(0.5)
    repeat -= 1


def bytes_to_string(size, decimals=0, use_binary=True):
  """Convert size into a human-readable format, returns str.

  [Doctest]
  >>> bytes_to_string(10)
  '10   B'
  >>> bytes_to_string(10_000_000)
  '10 MiB'
  >>> bytes_to_string(10_000_000, decimals=2)
  '9.54 MiB'
  >>> bytes_to_string(10_000_000, decimals=2, use_binary=False)
  '10.00 MB'
  >>> bytes_to_string(-10_000_000, decimals=4)
  '-9.5367 MiB'
  """
  LOG.debug(
    'size: %s, decimals: %s, use_binary: %s',
    size,
    decimals,
    use_binary,
    )
  size = float(size)
  abs_size = abs(size)

  # Set scale
  scale = 1000
  suffix = 'B'
  if use_binary:
    scale = 1024
    suffix = 'iB'

  # Convert to sensible units
  if abs_size >= scale ** 5:
    size /= scale ** 5
    units = 'P' + suffix
  elif abs_size >= scale ** 4:
    size /= scale ** 4
    units = 'T' + suffix
  elif abs_size >= scale ** 3:
    size /= scale ** 3
    units = 'G' + suffix
  elif abs_size >= scale ** 2:
    size /= scale ** 2
    units = 'M' + suffix
  elif abs_size >= scale ** 1:
    size /= scale ** 1
    units = 'K' + suffix
  else:
    size /= scale ** 0
    units = f' {" " if use_binary else ""}B'
  size = f'{size:0.{decimals}f} {units}'

  # Done
  LOG.debug('string: %s', size)
  return size


def choice(choices, prompt='答えろ！'):
  """Choose an option from a provided list, returns str.

  Choices provided will be converted to uppercase and returned as such.
  Similar to the commands choice (Windows) and select (Linux).
  """
  LOG.debug('choices: %s, prompt: %s', choices, prompt)
  answer = None
  choices = [str(c).upper()[:1] for c in choices]
  prompt = f'{prompt} [{"/".join(choices)}]'
  regex = f'^({"|".join(choices)})$'

  # Loop until acceptable answer is given
  while answer is None:
    tmp = input_text(prompt=prompt)
    if re.search(regex, tmp, re.IGNORECASE):
      answer = tmp.upper()

  # Done
  LOG.info('%s %s', prompt, answer)
  return answer


def clear_screen():
  """Simple wrapper for clear/cls."""
  cmd = 'cls' if os.name == 'nt' else 'clear'
  subprocess.run(cmd, check=False, shell=True, stderr=subprocess.PIPE)


def get_log_filepath():
  """Get the log filepath from the root logger, returns pathlib.Path obj.

  NOTE: This will use the first handler baseFilename it finds (if any).
  """
  log_filepath = None
  root_logger = logging.getLogger()

  # Check handlers
  for handler in root_logger.handlers:
    if hasattr(handler, 'baseFilename'):
      log_filepath = pathlib.Path(handler.baseFilename).resolve()
      break

  # Done
  return log_filepath


def generate_debug_report():
  """Generate debug report, returns str."""
  import socket
  platform_function_list = (
    'architecture',
    'machine',
    'platform',
    'python_version',
    )
  report = []

  # Logging data
  log_path = get_log_filepath()
  if log_path:
    report.append('------ Start Log -------')
    report.append('')
    with open(log_path, 'r') as log_file:
      report.extend(log_file.read().splitlines())
    report.append('')
    report.append('------- End Log --------')

  # System
  report.append('--- Start debug info ---')
  report.append('')
  report.append('[System]')
  report.append(f'  {"FQDN":<24} {socket.getfqdn()}')
  for func in platform_function_list:
    func_name = func.replace('_', ' ').capitalize()
    func_result = getattr(platform, func)()
    report.append(f'  {func_name:<24} {func_result}')
  report.append(f'  {"Python sys.argv":<24} {sys.argv}')
  report.append('')

  # Environment
  report.append('[Environment Variables]')
  for key, value in sorted(os.environ.items()):
    report.append(f'  {key:<24} {value}')
  report.append('')

  # Done
  report.append('---- End debug info ----')
  return '\n'.join(report)


def input_text(prompt='Enter text'):
  """Get text from user, returns string."""
  prompt = str(prompt)
  response = None
  if prompt[-1:] != ' ':
    prompt += ' '

  while response is None:
    if os.name == 'posix':
      # Flush input to (hopefully) avoid EOFError
      tcflush(sys.stdin, TCIOFLUSH)
    try:
      response = input(prompt)
      LOG.debug('%s%s', prompt, response)
    except EOFError:
      # Ignore and try again
      LOG.warning('Exception occured', exc_info=True)
      print('', flush=True)

  return response


def major_exception():
  """Display traceback, optionally upload detailes, and exit."""
  LOG.critical('Major exception encountered', exc_info=True)
  print_error('Major exception')
  print_warning(SUPPORT_MESSAGE)
  print(traceback.format_exc())

  # Build report
  report = generate_debug_report()

  # Upload details
  prompt = f'Upload details to {CRASH_SERVER.get("Name", "?")}?'
  if ENABLED_UPLOAD_DATA and ask(prompt):
    print('Uploading... ', end='', flush=True)
    try:
      upload_debug_report(report, reason='CRASH')
    except Exception: #pylint: disable=broad-except
      print_error('FAILED')
      LOG.error('Upload failed', exc_info=True)
    else:
      print_success('SUCCESS')
      LOG.info('Upload successful')

  # Done
  pause('Press Enter to exit... ')
  raise SystemExit(1)


def pause(prompt='Press Enter to continue... '):
  """Simple pause implementation."""
  input_text(prompt)


def print_colored(strings, colors, **kwargs):
  """Prints strings in the colors specified."""
  LOG.debug('strings: %s, colors: %s, kwargs: %s', strings, colors, kwargs)
  clear_code = COLORS['CLEAR']
  msg = ''
  print_options = {
    'end': kwargs.get('end', '\n'),
    'file': kwargs.get('file', sys.stdout),
    'flush': kwargs.get('flush', False),
    }

  # Build new string with color escapes added
  for string, color in itertools.zip_longest(strings, colors):
    color_code = COLORS.get(color, clear_code)
    msg += f'{color_code}{string}{clear_code}'

  print(msg, **print_options)


def print_error(msg, **kwargs):
  """Prints message in RED."""
  LOG.debug('msg: %s, kwargs: %s', msg, kwargs)
  if 'file' not in kwargs:
    # Only set if not specified
    kwargs['file'] = sys.stderr
  print_colored([msg], ['RED'], **kwargs)


def print_info(msg, **kwargs):
  """Prints message in BLUE."""
  LOG.debug('msg: %s, kwargs: %s', msg, kwargs)
  print_colored([msg], ['BLUE'], **kwargs)


def print_success(msg, **kwargs):
  """Prints message in GREEN."""
  LOG.debug('msg: %s, kwargs: %s', msg, kwargs)
  print_colored([msg], ['GREEN'], **kwargs)


def print_warning(msg, **kwargs):
  """Prints message in YELLOW."""
  LOG.debug('msg: %s, kwargs: %s', msg, kwargs)
  if 'file' not in kwargs:
    # Only set if not specified
    kwargs['file'] = sys.stderr
  print_colored([msg], ['YELLOW'], **kwargs)


def set_title(title):
  """Set window title."""
  if os.name == 'nt':
    os.system(f'title {title}')
  else:
    print_error('Setting the title is only supported under Windows.')


def sleep(seconds=2):
  """Simple wrapper for time.sleep."""
  time.sleep(seconds)


def string_to_bytes(size, assume_binary=False):
  """Convert human-readable size str to bytes and return an int."""
  LOG.debug('size: %s, assume_binary: %s', size, assume_binary)
  scale = 1000
  size = str(size)
  tmp = REGEX_SIZE_STRING.search(size.upper())

  # Raise exception if string can't be parsed as a size
  if not tmp:
    raise ValueError(f'Invalid size string: {size}')

  # Set scale
  if tmp.group('binary') or assume_binary:
    scale = 1024

  # Convert to bytes
  size = float(tmp.group('size'))
  units = tmp.group('units')
  if units == 'P':
    size *= scale ** 5
  if units == 'T':
    size *= scale ** 4
  elif units == 'G':
    size *= scale ** 3
  elif units == 'M':
    size *= scale ** 2
  elif units == 'K':
    size *= scale ** 1
  elif units == 'B':
    size *= scale ** 0
  size = int(size)

  # Done
  LOG.debug('bytes: %s', size)
  return size


def strip_colors(string):
  """Strip known ANSI color escapes from string, returns str."""
  LOG.debug('string: %s', string)
  for color in COLORS.values():
    string = string.replace(color, '')
  return string


def upload_debug_report(report, compress=True, reason='DEBUG'):
  """Upload debug report to CRASH_SERVER as specified in wk.cfg.main."""
  LOG.info('Uploading debug report to %s', CRASH_SERVER.get('Name', '?'))
  import requests
  headers = CRASH_SERVER.get('Headers', {'X-Requested-With': 'XMLHttpRequest'})
  if compress:
    headers['Content-Type'] = 'application/octet-stream'

  # Check if the required server details are available
  if not all(CRASH_SERVER.get(key, False) for key in ('Name', 'Url', 'User')):
    msg = 'Server details missing, aborting upload.'
    LOG.error(msg)
    print_error(msg)
    raise RuntimeError(msg)

  # Set filename (based on the logging config if possible)
  filename = 'Unknown'
  log_path = get_log_filepath()
  if log_path:
    # Strip everything but the prefix
    filename = re.sub(r'^(.*)_(\d{4}-\d{2}-\d{2}.*)', r'\1', log_path.name)
  filename = f'{filename}_{reason}_{time.strftime("%Y-%m-%d_%H%M%S%z")}.log'
  LOG.debug('filename: %s', filename)

  # Compress report
  if compress:
    filename += '.xz'
    xz_report = lzma.compress(report.encode('utf8'))

  # Upload report
  url = f'{CRASH_SERVER["Url"]}/{filename}'
  response = requests.put(
    url,
    data=xz_report if compress else report,
    headers=headers,
    auth=(CRASH_SERVER['User'], CRASH_SERVER.get('Pass', '')),
    )

  # Check response
  if not response.ok:
    raise RuntimeError('Failed to upload report')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
