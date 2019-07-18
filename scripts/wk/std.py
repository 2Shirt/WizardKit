'''WizardKit: Standard Functions'''
# vim: sts=2 sw=2 ts=2

import itertools
import logging
import os
import re
import sys
import time

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

  # Set scale
  scale = 1000
  suffix = 'B'
  if use_binary:
    scale = 1024
    suffix = 'iB'

  # Convert to sensible units
  if abs(size) >= scale ** 5:
    size /= scale ** 5
    units = 'P' + suffix
  elif abs(size) >= scale ** 4:
    size /= scale ** 4
    units = 'T' + suffix
  elif abs(size) >= scale ** 3:
    size /= scale ** 3
    units = 'G' + suffix
  elif abs(size) >= scale ** 2:
    size /= scale ** 2
    units = 'M' + suffix
  elif abs(size) >= scale ** 1:
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
  """Upload debug report to CRASH_SERVER as specified in wk.cfg.net."""
  import pathlib
  import requests
  from wk.cfg.net import CRASH_SERVER as server
  LOG.info('Uploading debug report to %s', server.get('Name', '?'))

  # Check if the required server details are available
  if not all(server.get(key, False) for key in ('Name', 'Url', 'User')):
    msg = 'Server details missing, aborting upload.'
    LOG.error(msg)
    print_error(msg)
    raise UserWarning(msg)

  # Set filename (based on the logging config if possible)
  ## NOTE: This is using a gross assumption on the logging setup
  ##       That's why there's such a broad exception if something goes wrong
  ## TODO: Test under all platforms
  root_logger = logging.getLogger()
  try:
    filename = root_logger.handlers[0].baseFilename
    filename = pathlib.Path(filename).name
    filename = re.sub(r'^(.*)_(\d{4}-\d{2}-\d{2}.*)', r'\1', filename)
  except Exception: #pylint: disable=broad-except
    filename = 'Unknown'
  filename = '{base}_{reason}_{datetime}.log'.format(
    base=filename,
    reason=reason,
    datetime=time.strftime('%Y-%m-%d_%H%M%S%z'),
    )
  LOG.debug('filename: %s', filename)

  # Upload report
  url = '{}/{}'.format(server['Url'], filename)
  response = requests.put(
    url,
    data=report,
    headers=server.get('Headers', {'X-Requested-With': 'XMLHttpRequest'}),
    auth=(server['User'], server.get('Pass', '')),
    )

  # Check response
  if not response.ok:
    # Using generic exception since we don't care why this failed
    raise Exception('Failed to upload report')


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
