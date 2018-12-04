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
QUICK_LABEL = '{YELLOW}(Quick){CLEAR}'.format(**COLORS)
SIDE_PATH_WIDTH = 21

# Classes
class DevObj():
  """Device object for tracking device specific data."""
  def __init__(self, dev_path):
    self.failing = False
    self.labels = []
    self.lsblk = {}
    self.name = re.sub(r'^.*/(.*)', r'\1', dev_path)
    self.nvme_attributes = {}
    self.override = False
    self.path = dev_path
    self.smart_attributes = {}
    self.smartctl = {}
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
    self.get_smart_details()

  def get_details(self):
    """Get data from lsblk."""
    cmd = ['lsblk', '--json', '--output-all', '--paths', self.path]
    try:
      result = run_program(cmd, check=False)
      json_data = json.loads(result.stdout.decode())
      self.lsblk = json_data['blockdevices'][0]
    except Exception:
      # Leave self.lsblk empty
      pass

    # Set necessary details
    self.lsblk['model'] = self.lsblk.get('model', 'Unknown Model')
    self.lsblk['name'] = self.lsblk.get('name', self.path)
    self.lsblk['rota'] = self.lsblk.get('rota', True)
    self.lsblk['serial'] = self.lsblk.get('serial', 'Unknown Serial')
    self.lsblk['size'] = self.lsblk.get('size', '???b')
    self.lsblk['tran'] = self.lsblk.get('tran', '???')

    # Ensure certain attributes are strings
    for attr in ['model', 'name', 'rota', 'serial', 'size', 'tran']:
      if not isinstance(self.lsblk[attr], str):
        self.lsblk[attr] = str(self.lsblk[attr])
    self.lsblk['tran'] = self.lsblk['tran'].upper().replace('NVME', 'NVMe')

    # Build list of labels
    for dev in [self.lsblk, *self.lsblk.get('children', [])]:
      self.labels.append(dev.get('label', ''))
      self.labels.append(dev.get('partlabel', ''))
    self.labels = [str(label) for label in self.labels if label]

  def get_smart_details(self):
    """Get data from smartctl."""
    cmd = ['sudo', 'smartctl', '--all', '--json', self.path]
    try:
      result = run_program(cmd, check=False)
      self.smartctl = json.loads(result.stdout.decode())
    except Exception:
      # Leave self.smartctl empty
      pass

    # Check for attributes
    if KEY_NVME in self.smartctl:
      self.nvme_attributes.update(self.smartctl[KEY_NVME])
    elif KEY_SMART in self.smartctl:
      for a in self.smartctl[KEY_SMART].get('table', {}):
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
    self.quick_mode = False
    self.started = False
    self.tests = {
      'Prime95 & Temps':  {'Enabled': False, 'Order': 1,
        'Result': None, 'Status': None},
      'NVMe / SMART':     {'Enabled': False, 'Order': 2},
      'badblocks':        {'Enabled': False, 'Order': 3},
      'I/O Benchmark':    {'Enabled': False, 'Order': 4},
    }
    self.add_devs()

  def add_devs(self):
    """Add all block devices listed by lsblk."""
    cmd = ['lsblk', '--json', '--nodeps', '--paths']
    result = run_program(cmd, check=False)
    json_data = json.loads(result.stdout.decode())
    for dev in json_data['blockdevices']:
      skip_dev = False
      dev_obj = DevObj(dev['name'])
      
      # Skip loopback devices
      if dev_obj.lsblk['tran'] == 'NONE':
        skip_dev = True
      
      # Skip WK devices
      wk_label_regex = r'{}_(LINUX|UFD)'.format(KIT_NAME_SHORT)
      for label in dev_obj.labels:
        if re.search(wk_label_regex, label, re.IGNORECASE):
          skip_dev = True
      
      # Add device
      if not skip_dev:
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

def menu_diags(state, args):
  """Main menu to select and run HW tests."""
  args = [a.lower() for a in args]
  title = '{GREEN}Hardware Diagnostics: Main Menu{CLEAR}'.format(
    **COLORS)
  # NOTE: Changing the order of main_options will break everything
  main_options = [
    {'Base Name': 'Full Diagnostic', 'Enabled': False},
    {'Base Name': 'Disk Diagnostic', 'Enabled': False},
    {'Base Name': 'Disk Diagnostic (Quick)', 'Enabled': False},
    {'Base Name': 'Prime95 & Temps', 'Enabled': False, 'CRLF': True},
    {'Base Name': 'NVMe / SMART', 'Enabled': False},
    {'Base Name': 'badblocks', 'Enabled': False},
    {'Base Name': 'I/O Benchmark', 'Enabled': False},
    ]
  actions = [
    {'Letter': 'A', 'Name': 'Audio Test'},
    {'Letter': 'K', 'Name': 'Keyboard Test'},
    {'Letter': 'N', 'Name': 'Network Test'},
    {'Letter': 'S', 'Name': 'Start', 'CRLF': True},
    {'Letter': 'Q', 'Name': 'Quit'},
    ]
  secret_actions = ['M', 'T']
  
  # Set initial selections
  update_main_options(state, '1', main_options)

  # CLI mode check
  if '--cli' in args or 'DISPLAY' not in global_vars['Env']:
    actions.append({'Letter': 'R', 'Name': 'Reboot'})
    actions.append({'Letter': 'P', 'Name': 'Power Off'})

  # Skip menu if running quick check
  if '--quick' in args:
    update_main_options(state, '3', main_options)
    state.quick_mode = True
    run_hw_tests(state)
    return True

  while True:
    # Set quick mode as necessary
    if main_options[2]['Enabled'] and main_options[4]['Enabled']:
      # Check if only Disk Diags (Quick) and NVMe/SMART are enabled
      # If so, verify no other tests are enabled and set quick_mode
      state.quick_mode = True
      for opt in main_options[3:4] + main_options[5:]:
        state.quick_mode &= not opt['Enabled']
    else:
      state.quick_mode = False

    # Deselect presets
    slice_end = 3
    if state.quick_mode:
      slice_end = 2
    for opt in main_options[:slice_end]:
      opt['Enabled'] = False

    # Verify preset selections
    num_tests_selected = 0
    for opt in main_options[3:]:
      if opt['Enabled']:
        num_tests_selected += 1
    if num_tests_selected == 4:
      # Full
      main_options[0]['Enabled'] = True
    elif num_tests_selected == 3 and not main_options[3]['Enabled']:
      # Disk
      main_options[1]['Enabled'] = True

    # Update checkboxes
    for opt in main_options:
      _nvme_smart = opt['Base Name'] == 'NVMe / SMART'
      opt['Name'] = '{} {} {}'.format(
        '[✓]' if opt['Enabled'] else '[ ]',
        opt['Base Name'],
        QUICK_LABEL if state.quick_mode and _nvme_smart else '')

    # Show menu
    selection = menu_select(
      title=title,
      main_entries=main_options,
      action_entries=actions,
      secret_actions=secret_actions,
      spacer='───────────────────────────────')

    if selection.isnumeric():
      update_main_options(state, selection, main_options)
    elif selection == 'A':
      run_audio_test()
    elif selection == 'K':
      run_keyboard_test()
    elif selection == 'N':
      run_network_test()
    elif selection == 'M':
      secret_screensaver('matrix')
    elif selection == 'T':
      # Tubes is close to pipes right?
      secret_screensaver('pipes')
    elif selection == 'R':
      run_program(['systemctl', 'reboot'])
    elif selection == 'P':
      run_program(['systemctl', 'poweroff'])
    elif selection == 'Q':
      break
    elif selection == 'S':
      run_hw_tests(state)

def run_audio_test():
  """Run audio test."""
  # TODO: Enable real test and remove placeholder
  clear_screen()
  print('Fake audio placeholder for now...')
  #run_program(['hw-diags-audio'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')

def run_hw_tests(state):
  """Run enabled hardware tests."""
  # Run test(s)
  clear_screen()
  print('Tests:')
  for k, v in sorted(
      state.tests.items(),
      key=lambda kv: kv[1]['Order']):
    print_standard('  {:<15} {}{}{} {}'.format(
      k,
      COLORS['GREEN'] if v['Enabled'] else COLORS['RED'],
      'Enabled' if v['Enabled'] else 'Disabled',
      COLORS['CLEAR'],
      QUICK_LABEL if state.quick_mode and 'NVMe' in k else ''))
  print('\nFake test(s) placeholder for now...')
  pause('Press Enter to return to main menu... ')

def run_keyboard_test():
  """Run keyboard test."""
  # TODO: Enable real test and remove placeholder
  clear_screen()
  print('Fake keyboard placeholder for now...')
  #run_program(['xev', '-event', 'keyboard'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')

def run_network_test():
  """Run network test."""
  # TODO: Enable real test and remove placeholder
  clear_screen()
  print('Fake network placeholder for now...')
  #run_program(['hw-diags-network'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')

def secret_screensaver(screensaver=None):
  """Show screensaver."""
  if screensaver == 'matrix':
    cmd = 'cmatrix -abs'.split()
  elif screensaver == 'pipes':
    cmd = 'pipes -t 0 -t 1 -t 2 -t 3 -p 5 -R -r 4000'.split()
  else:
    raise Exception('Invalid screensaver')
  run_program(cmd, check=False, pipe=False)

def update_main_options(state, selection, main_options):
  """Update menu and state based on selection."""
  index = int(selection) - 1
  main_options[index]['Enabled'] = not main_options[index]['Enabled']

  # Handle presets
  if index == 0:
    # Full
    if main_options[index]['Enabled']:
      for opt in main_options[1:3]:
        opt['Enabled'] = False
      for opt in main_options[3:]:
        opt['Enabled'] = True
    else:
      for opt in main_options[3:]:
        opt['Enabled'] = False
  elif index == 1:
    # Disk
    if main_options[index]['Enabled']:
      main_options[0]['Enabled'] = False
      for opt in main_options[2:4]:
        opt['Enabled'] = False
      for opt in main_options[4:]:
        opt['Enabled'] = True
    else:
      for opt in main_options[4:]:
        opt['Enabled'] = False
  elif index == 2:
    # Disk (Quick)
    if main_options[index]['Enabled']:
      for opt in main_options[:2] + main_options[3:]:
        opt['Enabled'] = False
      main_options[4]['Enabled'] = True
    else:
      main_options[4]['Enabled'] = False
  
  # Update state
  for opt in main_options[3:]:
    state.tests[opt['Base Name']]['Enabled'] = opt['Enabled']
  
  # Done
  return main_options

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
