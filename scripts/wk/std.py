'''WizardKit: Standard Functions'''
# vim: sts=2 sw=2 ts=2

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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
