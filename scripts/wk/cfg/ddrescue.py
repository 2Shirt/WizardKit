"""WizardKit: Config - ddrescue"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2

import re

from collections import OrderedDict


# General
MAP_DIR = '/Backups/ddrescue-tui'
RECOMMENDED_FSTYPES = ['ext3', 'ext4', 'xfs']
RECOMMENDED_MAP_FSTYPES = ['cifs', 'ext2', 'ext3', 'ext4', 'vfat', 'xfs']

# Layout
TMUX_SIDE_WIDTH = 21
TMUX_LAYOUT = OrderedDict({
  'Source':   {'height':  2,                'Check': True},
  'Started':  {'width':   TMUX_SIDE_WIDTH,  'Check': True},
  'Progress': {'width':   TMUX_SIDE_WIDTH,  'Check': True},
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
REGEX_DDRESCUE_LOG = re.compile(
  r'^\s*(?P<key>\S+):\s+'
  r'(?P<size>\d+)\s+'
  r'(?P<unit>[PTGMKB])i?B?',
  re.IGNORECASE,
  )
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
