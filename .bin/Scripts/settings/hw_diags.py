# Wizard Kit: Settings - HW Diagnostics

# General
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
    'critical_warning': {'Error':   1, 'Critical': True},
    'media_errors':     {'Error':   1, 'Critical': True},
    'power_on_hours':   {'Warning': 12000, 'Error': 26298, 'Ignore': True},
    'unsafe_shutdowns': {'Warning': 1},
    },
  'SMART': {
    5:    {'Hex': '05', 'Error':   1, 'Critical': True},
    9:    {'Hex': '09', 'Warning': 12000, 'Error': 26298, 'Ignore': True},
    10:   {'Hex': '0A', 'Error':   1},
    184:  {'Hex': 'B8', 'Error':   1},
    187:  {'Hex': 'BB', 'Error':   1},
    188:  {'Hex': 'BC', 'Error':   1},
    196:  {'Hex': 'C4', 'Error':   1},
    197:  {'Hex': 'C5', 'Error':   1, 'Critical': True},
    198:  {'Hex': 'C6', 'Error':   1, 'Critical': True},
    199:  {'Hex': 'C7', 'Error':   1, 'Ignore': True},
    201:  {'Hex': 'C9', 'Error':   1},
    },
  }
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'

# Tests: Prime95
MPRIME_LIMIT = 7    # of minutes to run Prime95
THERMAL_LIMIT = 95  # Abort temperature in Celsius


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2 tw=0
