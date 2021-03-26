"""WizardKit: Config - ddrescue"""
# pylint: disable=line-too-long
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
AUTO_PASS_THRESHOLDS = {
  # NOTE: The scrape key is set to infinity to force a break
  'read': 95,
  'trim': 98,
  'scrape': float('inf'),
  }
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
PARTITION_TYPES = {
  'GPT': {
    'NTFS':   'EBD0A0A2-B9E5-4433-87C0-68B6B72699C7', # Basic Data Partition
    'VFAT':   'EBD0A0A2-B9E5-4433-87C0-68B6B72699C7', # Basic Data Partition
    'EXFAT':  'EBD0A0A2-B9E5-4433-87C0-68B6B72699C7', # Basic Data Partition
    },
  'MBR': {
    'EXFAT':  '7',
    'NTFS':   '7',
    'VFAT':   'b',
    },
  }


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
