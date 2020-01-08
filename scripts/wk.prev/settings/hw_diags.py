# Wizard Kit: Settings - HW Diagnostics

from collections import OrderedDict

# General
DEBUG_MODE = False
OVERRIDES_FORCED = False
OVERRIDES_LIMITED = True # If True this disables OVERRIDE_FORCED
STATUSES = {
  'RED':    ['Denied', 'ERROR', 'NS', 'TimedOut'],
  'YELLOW': ['Aborted', 'N/A', 'OVERRIDE', 'Unknown', 'Working'],
  'GREEN':  ['CS'],
}
TESTS_CPU = ['Prime95']
TESTS_DISK = [
  'I/O Benchmark',
  'NVMe / SMART',
  'badblocks',
  ]

# Layout
## NOTE: Colors will be applied in functions/hw_diags.py
QUICK_LABEL = '{YELLOW}(Quick){CLEAR}'
SIDE_PANE_WIDTH = 20
TOP_PANE_TEXT = '{GREEN}Hardware Diagnostics{CLEAR}'
TMUX_LAYOUT = OrderedDict({
  'Top':            {'y': 2,                'Check': True},
  'Started':        {'x': SIDE_PANE_WIDTH,  'Check': True},
  'Progress':       {'x': SIDE_PANE_WIDTH,  'Check': True},
  # Testing panes
  'Prime95':        {'y': 11,               'Check': False},
  'Temps':          {'y': 1000,             'Check': False},
  'SMART':          {'y': 3,                'Check': True},
  'badblocks':      {'y': 5,                'Check': True},
  'I/O Benchmark':  {'y': 1000,             'Check': False},
})

# Tests: badblocks
## NOTE: Force 4K read block size for disks >= to 3TB
BADBLOCKS_LARGE_DISK = 3*1024**4

# Tests: I/O Benchmark
IO_VARS = {
  'Block Size': 512*1024,
  'Chunk Size': 32*1024**2,
  'Minimum Test Size': 10*1024**3,
  'Alt Test Size Factor': 0.01,
  'Progress Refresh Rate': 5,
  'Scale 8': [2**(0.56*(x+1))+(16*(x+1)) for x in range(8)],
  'Scale 16': [2**(0.56*(x+1))+(16*(x+1)) for x in range(16)],
  'Scale 32': [2**(0.56*(x+1)/2)+(16*(x+1)/2) for x in range(32)],
  'Threshold Graph Fail': 65*1024**2,
  'Threshold Graph Warn': 135*1024**2,
  'Threshold Graph Great': 750*1024**2,
  'Threshold HDD Min': 50*1024**2,
  'Threshold HDD High Avg': 75*1024**2,
  'Threshold HDD Low Avg': 65*1024**2,
  'Threshold SSD Min': 90*1024**2,
  'Threshold SSD High Avg': 135*1024**2,
  'Threshold SSD Low Avg': 100*1024**2,
  'Graph Horizontal': ('▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'),
  'Graph Horizontal Width': 40,
  'Graph Vertical': (
    '▏',    '▎',    '▍',    '▌',
    '▋',    '▊',    '▉',    '█',
    '█▏',   '█▎',   '█▍',   '█▌',
    '█▋',   '█▊',   '█▉',   '██',
    '██▏',  '██▎',  '██▍',  '██▌',
    '██▋',  '██▊',  '██▉',  '███',
    '███▏', '███▎', '███▍', '███▌',
    '███▋', '███▊', '███▉', '████'),
  }

# Tests: NVMe/SMART
ATTRIBUTES = {
  'NVMe': {
    'critical_warning': {'Critical': True,  'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
    'media_errors':     {'Critical': True,  'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
    'power_on_hours':   {'Critical': False, 'Ignore': True,   'Warning': 17532, 'Error': 26298, 'Maximum': None,  },
    'unsafe_shutdowns': {'Critical': False, 'Ignore': True,   'Warning': 1,     'Error': None,  'Maximum': None,  },
    },
  'SMART': {
    5:    {'Hex': '05', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
    9:    {'Hex': '09', 'Critical': False,  'Ignore': True,   'Warning': 17532, 'Error': 26298, 'Maximum': None,  },
    10:   {'Hex': '10', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
    184:  {'Hex': 'B8', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
    187:  {'Hex': 'BB', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
    188:  {'Hex': 'BC', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
    196:  {'Hex': 'C4', 'Critical': False,  'Ignore': False,  'Warning': 1,     'Error': 10,    'Maximum': 10000, },
    197:  {'Hex': 'C5', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
    198:  {'Hex': 'C6', 'Critical': True,   'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': None,  },
    199:  {'Hex': 'C7', 'Critical': False,  'Ignore': True,   'Warning': None,  'Error': 1,     'Maximum': None,  },
    201:  {'Hex': 'C9', 'Critical': False,  'Ignore': False,  'Warning': None,  'Error': 1,     'Maximum': 10000, },
    },
  }
ATTRIBUTE_COLORS = (
  # NOTE: The order here is important; least important to most important.
  ('Warning', 'YELLOW'),
  ('Error', 'RED'),
  ('Maximum', 'PURPLE'),
  )
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'

# Tests: Prime95
MPRIME_LIMIT = 7    # of minutes to run Prime95
THERMAL_LIMIT = 95  # Abort temperature in Celsius


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2 tw=0
