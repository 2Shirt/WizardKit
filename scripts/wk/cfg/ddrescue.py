"""WizardKit: Config - ddrescue"""
# pylint: disable=bad-whitespace,line-too-long
# vim: sts=2 sw=2 ts=2

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
    '--reverse':          {'Selected': False,                               },
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


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
