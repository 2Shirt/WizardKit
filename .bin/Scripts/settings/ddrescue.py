# Wizard Kit: Settings - ddrescue-tui

import re

from collections import OrderedDict

# General
RECOMMENDED_FSTYPES = ['ext3', 'ext4', 'xfs']
USAGE = """  {script_name} clone [source [destination]]
  {script_name} image [source [destination]]
  (e.g. {script_name} clone /dev/sda /dev/sdb)
"""

# Layout
SIDE_PANE_WIDTH = 21
TMUX_LAYOUT = OrderedDict({
  'Source':   {'y': 2,         'Check': True},
  'Started':  {'x': SIDE_PANE_WIDTH, 'Check': True},
  'Progress': {'x': SIDE_PANE_WIDTH, 'Check': True},
})

# ddrescue
AUTO_PASS_1_THRESHOLD = 95
AUTO_PASS_2_THRESHOLD = 98
DDRESCUE_SETTINGS = {
  '--binary-prefixes':  {'Enabled': True,                 'Hidden': True, },
  '--data-preview':     {'Enabled': True,   'Value': '5', 'Hidden': True, },
  '--idirect':          {'Enabled': True,                                 },
  '--odirect':          {'Enabled': True,                                 },
  '--max-read-rate':    {'Enabled': False,  'Value': '1MiB',              },
  '--min-read-rate':    {'Enabled': True,   'Value': '64KiB',             },
  '--reopen-on-error':  {'Enabled': True,                                 },
  '--retry-passes':     {'Enabled': True,   'Value': '0',                 },
  '--test-mode':        {'Enabled': False,  'Value': 'test.map',          },
  '--timeout':          {'Enabled': True,   'Value': '5m',                },
  '-vvvv':              {'Enabled': True,                 'Hidden': True, },
  }
ETOC_REFRESH_RATE = 30 # in seconds
REGEX_REMAINING_TIME = re.compile(
  r'remaining time:'
  r'\s*((?P<days>\d+)d)?'
  r'\s*((?P<hours>\d+)h)?'
  r'\s*((?P<minutes>\d+)m)?'
  r'\s*((?P<seconds>\d+)s)?'
  r'\s*(?P<na>n/a)?',
  re.IGNORECASE
  )


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
