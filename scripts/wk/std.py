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


def print_standard(msg, **kwargs):
  """Prints message."""
  LOG.debug('msg: %s, kwargs: %s', msg, kwargs)
  print_colored([msg], [None], **kwargs)


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


def strip_colors(string):
  """Strip known ANSI color escapes from string, returns str."""
  LOG.debug('string: %s', string)
  for color in COLORS.values():
    string = string.replace(color, '')
  return string


def sleep(seconds=2):
  """Simple wrapper for time.sleep."""
  time.sleep(seconds)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
