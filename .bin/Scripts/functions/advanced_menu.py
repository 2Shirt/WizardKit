'''Wizard Kit: Functions - Advanced Menu'''
# vim: sts=2 sw=2 ts=2

import os
from collections import OrderedDict

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
VALID_ENTRY_TYPES = (
  'Action',
  'Option',
  'Set',
  'Toggle',
  )


# Classes
class MenuEntry():
  """Class for advanced menu entries"""
  # pylint: disable=too-few-public-methods
  def __init__(self, **kwargs):
    kwargs = {str(k).lower(): v for k, v in kwargs.items()}
    self.name = kwargs.pop('name', None)
    self.type = kwargs.pop('type', None)
    self.disabled = kwargs.pop('disabled', False)
    self.hidden = kwargs.pop('hidden', False)
    self.selected = kwargs.pop('selected', False)
    self.separator = kwargs.pop('separator', False)

    # Other attributes
    for _key, _value in kwargs.items():
      setattr(self, _key, kwargs.get(_key))
    del kwargs

    # Check attributes
    self.check()

  def check(self):
    """Check for invalid or missing attributes."""
    assert self.name, 'Invalid menu entry name.'
    assert self.type in VALID_ENTRY_TYPES, 'Invalid menu entry type.'


class MenuState():
  """Class to track various parts of the advanced menu."""
  def __init__(self, title):
    self.checkmark = '✓' if 'DISPLAY' in os.environ else '*'
    self.entries = OrderedDict({})
    self.last_sel = None
    self.sep = '─'
    self.sep_len = 0
    self.title = title

  def add_entry(self, **kwargs):
    """Add entry and update state."""
    _e = MenuEntry(**kwargs)
    assert _e.name not in self.entries, 'Duplicate menu entry.'

    # Add to entries
    self.entries[_e.name] = _e

    # Update sep length
    self.sep_len = max(len(_e.name), self.sep_len)

  def make_single_selection(self):
    """Select single entry."""
    _sep_len = self.sep_len + 3
    display_list = [self.title, '']
    valid_answers = {}

    # Safety Check
    assert self.entries, 'No menu entries defined.'

    # Reset selections
    for entry in self.entries.values():
      entry.selected = False

    # Build Menu
    i = 1
    for name, entry in self.entries.items():
      # Skip sets
      if entry.type in ('Set', 'Toggle'):
        continue

      # Separators
      if entry.separator:
        display_list.append(self.sep * _sep_len)

      # Entries
      _prefix = None
      if entry.type == 'Option':
        _prefix = str(i)
        i += 1
      elif entry.type == 'Action':
        _prefix = name[0:1].upper()
      display_list.append('{}: {}'.format(_prefix, name))
      valid_answers[_prefix] = name

      # Disable entry if necessary
      if entry.disabled:
        display_list[-1] = '{ORANGE}{text}{CLEAR}'.format(
          text=display_list[-1],
          **COLORS,
          )
        valid_answers.pop(_prefix)

      # Hide action entry if necessary
      if entry.type == 'Action' and entry.hidden:
        display_list.pop()

    # Show Menu and make selection
    _answer = ''
    while _answer.upper() not in valid_answers:
      clear()
      print('\n'.join(display_list))
      _answer = input('Please make a selection: ')

    # Mark and save selection
    self.entries[valid_answers[_answer.upper()]].selected = True
    self.last_sel = valid_answers[_answer.upper()]

  def make_multiple_selections(self):
    """Select one or more entries."""
    _sep_len = self.sep_len + 7
    # TODO

# Functions
def clear():
  """Simple wrapper for cls/clear."""
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

if __name__ == '__main__':
  print('This file is not meant to be called directly.')
