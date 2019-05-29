'''Wizard Kit: Functions - Advanced Menu'''
# vim: sts=2 sw=2 ts=2

import os
from collections import OrderedDict

# Classes
class MenuState():
  """Class to track various parts of a menu."""
  def __init__(self, title):
    self.checkmark = '✓' if 'DISPLAY' in os.environ else '*'
    self.entries = OrderedDict({})
    self.last_sel = None
    self.sep = '─'
    self.sep_len = 0
    self.title = title

  def add_entry(self, name, kind, **kwargs):
    """Add entry and update state."""
    if name in self.entries:
      raise Exception('Entry {} already exists.'.format(name))

    # Add to entries
    self.entries[name] = {
      'Kind': kind,
      'Selected': False,
      'Disabled': kwargs.get('Disabled', False),
      }
    self.entries[name].update(**kwargs)

    # Update sep length
    self.sep_len = max(len(name), self.sep_len)

  def make_single_selection(self):
    """Select single entry."""
    _sep_len = self.sep_len + 3
    display_list = [self.title, '']
    valid_answers = {}

    # Safety Check
    assert self.entries, "No menu entries defined."

    # Build Menu
    i = 1
    for name, details in self.entries.items():
      # Skip sets
      if details['Kind'] in ('Set', 'Toggle'):
        continue

      # Separators
      if details.get('Separator', False):
        display_list.append(self.sep * _sep_len)

      # Entries
      _prefix = None
      if details['Kind'] == 'Option':
        _prefix = str(i)
        i += 1
      elif details['Kind'] == 'Action':
        _prefix = name[0:1].upper()
      display_list.append('{}: {}'.format(_prefix, name))
      valid_answers[_prefix] = name

    # Show Menu and make selection
    _answer = ''
    while _answer.upper() not in valid_answers:
      clear()
      print('\n'.join(display_list))
      _answer = input('Please make a selection: ')

    # Save last selection
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
  print("This file is not meant to be called directly.")
