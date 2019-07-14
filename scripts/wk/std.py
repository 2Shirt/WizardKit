'''WizardKit: Standard Functions'''
# vim: sts=2 sw=2 ts=2

import itertools
import logging
import os
import re
import sys

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
def ask(prompt='Kotaero!'):
  """Prompt the user with a Y/N question, returns bool."""
  answer = None
  prompt = '{} [Y/N]: '.format(prompt)
  while answer is None:
    tmp = input_text(prompt)
    if re.search(r'^y(es|)$', tmp, re.IGNORECASE):
      answer = True
    elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
      answer = False
  LOG.info('%s%s', prompt, 'Yes' if answer else 'No')
  return answer


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
  """Prints strings in the colors specified and adds to log."""
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
  LOG.log(
    level=logging.getLevelName(kwargs.get('level', 'INFO')),
    msg=''.join(strings),
    )


def print_error(msg, **kwargs):
  """Prints message in RED and adds to log."""
  print_colored([mgs], ['RED'], level='ERROR', **kwargs)


def print_info(msg, **kwargs):
  """Prints message in BLUE and adds to log."""
  print_colored([mgs], ['BLUE'], **kwargs)


def print_standard(msg, **kwargs):
  """Prints message and adds to log."""
  print_colored([mgs], [None], **kwargs)


def print_success(msg, **kwargs):
  """Prints message in GREEN and adds to log."""
  print_colored([mgs], ['GREEN'], **kwargs)


def print_warning(msg, **kwargs):
  """Prints message in YELLOW and adds to log."""
  print_colored([mgs], ['YELLOW'], level='WARNING', **kwargs)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
