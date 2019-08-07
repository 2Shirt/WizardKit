'''WizardKit: Standard Functions'''
# vim: sts=2 sw=2 ts=2

import itertools
import logging
import os
import pathlib
import platform
import re
import sys
import time
import traceback

from wk.cfg.main import CRASH_SERVER, ENABLED_UPLOAD_DATA, SUPPORT_MESSAGE

try:
  from termios import tcflush, TCIOFLUSH
except ImportError:
  if os.name == 'posix':
    raise


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
  prompt = '{} [Y/N]: '.format(prompt)

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
  """Convert size into a human-readable format, returns str."""
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
    units = ' {}B'.format(' ' if use_binary else '')
  size = '{size:0.{decimals}f} {units}'.format(
    size=size,
    decimals=decimals,
    units=units,
    )

  # Done
  LOG.debug('string: %s', size)
  return size


def choice(choices, prompt='答えろ！'):
  """Choose an option from a provided list, returns str.

  Choices provided will be converted to uppercase and returned as such.
  Similar to the commands choice (Windows) and select (Linux)."""
  LOG.debug('choices: %s, prompt: %s', choices, prompt)
  answer = None
  choices = [str(c).upper()[:1] for c in choices]
  prompt = '{} [{}]: '.format(prompt, '/'.join(choices))
  regex = '^({})$'.format('|'.join(choices))

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
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')


def get_log_filepath():
  """Get the log filepath from the root logger, returns pathlib.Path obj.

  NOTE: This will use the first handler baseFilename it finds (if any)."""
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
  report.append('  {:<24} {}'.format('FQDN', socket.getfqdn()))
  for func in platform_function_list:
    func_name = func.replace('_', ' ').capitalize()
    func_result = getattr(platform, func)()
    report.append('  {:<24} {}'.format(func_name, func_result))
  report.append('  {:<24} {}'.format('Python sys.argv', sys.argv))
  report.append('')

  # Environment
  report.append('[Environment Variables]')
  for key, value in sorted(os.environ.items()):
    report.append('  {:<24} {}'.format(key, value))
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
  ## TODO
  report = 'TODO\n'

  # Upload details
  prompt = 'Upload details to {}?'.format(
    CRASH_SERVER.get('Name', '?'),
    )
  if ENABLED_UPLOAD_DATA and ask(prompt):
    print('Uploading... ', end='', flush=True)
    try:
      upload_debug_report(report, reason='CRASH')
    except Exception: #pylint: disable=broad-except
      print_colored(['FAILED'], ['RED'])
      LOG.error('Upload failed')
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
  msg = ''
  print_options = {
    'end': kwargs.get('end', '\n'),
    'file': kwargs.get('file', sys.stdout),
    'flush': kwargs.get('flush', False),
    }

  # Build new string with color escapes added
  for string, color in itertools.zip_longest(strings, colors):
    msg += '{}{}{}'.format(
      COLORS.get(color, COLORS['CLEAR']),
      string,
      COLORS['CLEAR'],
      )

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
    os.system('title {}'.format(title))
  else:
    raise NotImplementedError


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
    raise ValueError('invalid size string: {}'.format(size))

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


def upload_debug_report(report, reason='DEBUG'):
  """Upload debug report to CRASH_SERVER as specified in wk.cfg.main."""
  import requests
  LOG.info('Uploading debug report to %s', CRASH_SERVER.get('Name', '?'))

  # Check if the required server details are available
  if not all(CRASH_SERVER.get(key, False) for key in ('Name', 'Url', 'User')):
    msg = 'Server details missing, aborting upload.'
    LOG.error(msg)
    print_error(msg)
    raise UserWarning(msg)

  # Set filename (based on the logging config if possible)
  filename = 'Unknown'
  log_path = get_log_filepath()
  if log_path:
    # Strip everything but the prefix
    filename = re.sub(r'^(.*)_(\d{4}-\d{2}-\d{2}.*)', r'\1', log_path.name)
  filename = '{prefix}_{reason}_{datetime}.log'.format(
    prefix=filename,
    reason=reason,
    datetime=time.strftime('%Y-%m-%d_%H%M%S%z'),
    )
  LOG.debug('filename: %s', filename)

  # Upload report
  url = '{}/{}'.format(CRASH_SERVER['Url'], filename)
  response = requests.put(
    url,
    data=report,
    headers=CRASH_SERVER.get(
      'Headers',
      {'X-Requested-With': 'XMLHttpRequest'},
      ),
    auth=(CRASH_SERVER['User'], CRASH_SERVER.get('Pass', '')),
    )

  # Check response
  if not response.ok:
    # Using generic exception since we don't care why this failed
    raise Exception('Failed to upload report')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
