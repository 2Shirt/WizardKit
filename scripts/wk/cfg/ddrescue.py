"""WizardKit: Config - ddrescue"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2

import re

from collections import OrderedDict


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
  'Default': {
    '--binary-prefixes':  {'Selected': True,                'Hidden': True, },
    '--data-preview':     {'Selected': True,  'Value': '5', 'Hidden': True, },
    '--idirect':          {'Selected': True,                                },
    '--odirect':          {'Selected': True,                                },
    '--max-error-rate':   {'Selected': True,  'Value': '100MiB',            },
    '--max-read-rate':    {'Selected': False, 'Value': '1MiB',              },
    '--min-read-rate':    {'Selected': True,  'Value': '64KiB',             },
    '--reopen-on-error':  {'Selected': True,                                },
    '--retry-passes':     {'Selected': True,  'Value': '0',                 },
    '--test-mode':        {'Selected': False, 'Value': 'test.map',          },
    '--timeout':          {'Selected': True,  'Value': '30m',               },
    '-vvvv':              {'Selected': True,                'Hidden': True, },
    },
  'Fast': {
    '--max-error-rate':   {'Selected': True,  'Value': '32MiB',             },
    '--min-read-rate':    {'Selected': True,  'Value': '1MiB',              },
    '--reopen-on-error':  {'Selected': False,                               },
    '--timeout':          {'Selected': True,  'Value': '5m',                },
    },
  'Safe': {
    '--max-read-rate':    {'Selected': True,  'Value': '64MiB',             },
    '--min-read-rate':    {'Selected': True,  'Value': '1KiB',              },
    '--reopen-on-error':  {'Selected': True,                                },
    '--timeout':          {'Selected': False, 'Value': '30m',               },
    },
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
