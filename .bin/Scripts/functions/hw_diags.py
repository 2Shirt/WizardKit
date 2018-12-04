# Wizard Kit: Functions - HW Diagnostics

import json
import re
import time

from functions.common import *

# STATIC VARIABLES
ATTRIBUTES = {
  'NVMe': {
    'critical_warning': {'Error':   1},
    'media_errors':     {'Error':   1},
    'power_on_hours':   {'Warning': 12000, 'Error': 26298, 'Ignore': True},
    'unsafe_shutdowns': {'Warning': 1},
    },
  'SMART': {
    5:   {'Hex': '05', 'Error':   1},
    9:   {'Hex': '09', 'Warning': 12000, 'Error': 26298, 'Ignore': True},
    10:  {'Hex': '0A', 'Error':   1},
    184: {'Hex': 'B8', 'Error':   1},
    187: {'Hex': 'BB', 'Error':   1},
    188: {'Hex': 'BC', 'Error':   1},
    196: {'Hex': 'C4', 'Error':   1},
    197: {'Hex': 'C5', 'Error':   1},
    198: {'Hex': 'C6', 'Error':   1},
    199: {'Hex': 'C7', 'Error':   1, 'Ignore': True},
    201: {'Hex': 'C9', 'Error':   1},
    },
  }
IO_VARS = {
  'Block Size': 512*1024,
  'Chunk Size': 32*1024**2,
  'Minimum Dev Size': 8*1024**3,
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
KEY_NVME = 'nvme_smart_health_information_log'
KEY_SMART = 'ata_smart_attributes'
SIDE_PATH_WIDTH = 21

# Classes
class DevObj():
  """Device object for tracking device specific data."""
  def __init__(self, dev_path):
    self.failing = False
    self.nvme_attributes = {}
    self.override = False
    self.path = dev_path
    self.smart_attributes = {}
    self.tests = {
      'NVMe / SMART':   {'Result': None, 'Status': None},
      'badblocks':      {'Result': None, 'Status': None},
      'I/O Benchmark':  {
        'Result': None,
        'Status': None,
        'Read Rates': [],
        'Graph Data': []},
    }
    self.get_details()

  def get_details(self):
    """Get data from smartctl."""
    cmd = ['sudo', 'smartctl', '--all', '--json', self.path]
    result = run_program(cmd, check=False)
    self.data = json.loads(result.stdout.decode())

    # Check for attributes
    if KEY_NVME in self.data:
      self.nvme_attributes.update(self.data[KEY_NVME])
    elif KEY_SMART in self.data:
      for a in self.data[KEY_SMART].get('table', {}):
        _id = str(a.get('id', 'UNKNOWN'))
        _name = str(a.get('name', 'UNKNOWN'))
        _raw = a.get('raw', {}).get('value', -1)
        _raw_str = a.get('raw', {}).get('string', 'UNKNOWN')

        # Fix power-on time
        _r = re.match(r'^(\d+)[Hh].*', _raw_str)
        if _id == '9' and _r:
          try:
            _raw = int(_r.group(1))
          except ValueError:
            # That's fine
            pass
        self.smart_attributes[_id] = {
          'name': _name, 'raw': _raw, 'raw_str': _raw_str}

class State():
  """Object to track device objects and overall state."""
  def __init__(self):
    self.devs = []
    self.finished = False
    self.progress_out = '{}/progress.out'.format(global_vars['LogDir'])
    self.started = False
    self.tests = {
      'Prime95':        {'Enabled': False, 'Result': None, 'Status': None},
      'NVMe / SMART':   {'Enabled': False},
      'badblocks':      {'Enabled': False},
      'I/O Benchmark':  {'Enabled': False},
    }
    self.add_devs()

  def add_devs(self):
    """Add all block devices listed by lsblk."""
    cmd = ['lsblk', '--json', '--nodeps', '--paths']
    result = run_program(cmd, check=False)
    json_data = json.loads(result.stdout.decode())
    for dev in json_data['blockdevices']:
      self.devs.append(DevObj(dev['name']))

# Functions
def generate_horizontal_graph(rates, oneline=False):
  """Generate two-line horizontal graph from rates, returns str."""
  line_1 = ''
  line_2 = ''
  line_3 = ''
  line_4 = ''
  for r in rates:
    step = get_graph_step(r, scale=32)
    if oneline:
      step = get_graph_step(r, scale=8)

    # Set color
    r_color = COLORS['CLEAR']
    if r < IO_VARS['Threshold Graph Fail']:
      r_color = COLORS['RED']
    elif r < IO_VARS['Threshold Graph Warn']:
      r_color = COLORS['YELLOW']
    elif r > IO_VARS['Threshold Graph Great']:
      r_color = COLORS['GREEN']

    # Build graph
    full_block = '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][-1])
    if step >= 24:
      line_1 += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-24])
      line_2 += full_block
      line_3 += full_block
      line_4 += full_block
    elif step >= 16:
      line_1 += ' '
      line_2 += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-16])
      line_3 += full_block
      line_4 += full_block
    elif step >= 8:
      line_1 += ' '
      line_2 += ' '
      line_3 += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-8])
      line_4 += full_block
    else:
      line_1 += ' '
      line_2 += ' '
      line_3 += ' '
      line_4 += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step])
  line_1 += COLORS['CLEAR']
  line_2 += COLORS['CLEAR']
  line_3 += COLORS['CLEAR']
  line_4 += COLORS['CLEAR']
  if oneline:
    return line_4
  else:
    return '\n'.join([line_1, line_2, line_3, line_4])

def get_graph_step(rate, scale=16):
  """Get graph step based on rate and scale, returns int."""
  m_rate = rate / (1024**2)
  step = 0
  scale_name = 'Scale {}'.format(scale)
  for x in range(scale-1, -1, -1):
    # Iterate over scale backwards
    if m_rate >= IO_VARS[scale_name][x]:
      step = x
      break
  return step

def get_read_rate(s):
  """Get read rate in bytes/s from dd progress output."""
  real_rate = None
  if re.search(r'[KMGT]B/s', s):
    human_rate = re.sub(r'^.*\s+(\d+\.?\d*)\s+(.B)/s\s*$', r'\1 \2', s)
    real_rate = convert_to_bytes(human_rate)
  return real_rate

def get_status_color(s):
  """Get color based on status, returns str."""
  color = COLORS['CLEAR']
  if s in ['Denied', 'ERROR', 'NS', 'OVERRIDE']:
    color = COLORS['RED']
  elif s in ['Aborted', 'Unknown', 'Working', 'Skipped']:
    color = COLORS['YELLOW']
  elif s in ['CS']:
    color = COLORS['GREEN']
  return color

def update_io_progress(percent, rate, progress_file):
  """Update I/O progress file."""
  bar_color = COLORS['CLEAR']
  rate_color = COLORS['CLEAR']
  step = get_graph_step(rate, scale=32)
  if rate < IO_VARS['Threshold Graph Fail']:
    bar_color = COLORS['RED']
    rate_color = COLORS['YELLOW']
  elif rate < IO_VARS['Threshold Graph Warn']:
    bar_color = COLORS['YELLOW']
    rate_color = COLORS['YELLOW']
  elif rate > IO_VARS['Threshold Graph Great']:
    bar_color = COLORS['GREEN']
    rate_color = COLORS['GREEN']
  line = '  {p:5.1f}%  {b_color}{b:<4}  {r_color}{r:6.1f} Mb/s{c}\n'.format(
    p=percent,
    b_color=bar_color,
    b=IO_VARS['Graph Vertical'][step],
    r_color=rate_color,
    r=rate/(1024**2),
    c=COLORS['CLEAR'])
  with open(progress_file, 'a') as f:
    f.write(line)

if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
