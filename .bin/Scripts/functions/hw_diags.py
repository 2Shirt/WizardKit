# Wizard Kit: Functions - HW Diagnostics

import json
import re
import time

from collections import OrderedDict
from functions.sensors import *
from functions.tmux import *

# STATIC VARIABLES
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
HW_OVERRIDES_FORCED = HW_OVERRIDES_FORCED and not HW_OVERRIDES_LIMITED
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
SIDE_PANE_WIDTH = 20
TESTS_CPU = ['Prime95']
TESTS_DISK = [
  'I/O Benchmark',
  'NVMe / SMART',
  'badblocks',
  ]
TOP_PANE_TEXT = '{GREEN}Hardware Diagnostics{CLEAR}'.format(**COLORS)

# Classes
class CpuObj():
  """Object for tracking CPU specific data."""
  def __init__(self):
    self.lscpu = {}
    self.tests = {}
    self.get_details()
    self.name = self.lscpu.get('Model name', 'Unknown CPU')

  def get_details(self):
    """Get CPU details from lscpu."""
    cmd = ['lscpu', '--json']
    try:
      result = run_program(cmd, check=False)
      json_data = json.loads(result.stdout.decode())
    except Exception:
      # Ignore and leave self.lscpu empty
      return
    for line in json_data.get('lscpu', []):
      _field = line.get('field', None).replace(':', '')
      _data = line.get('data', None)
      if not _field and not _data:
        # Skip
        print_warning(_field, _data)
        pause()
        continue
      self.lscpu[_field] = _data

class DiskObj():
  """Object for tracking disk specific data."""
  def __init__(self, disk_path):
    self.disk_ok = True
    self.labels = []
    self.lsblk = {}
    self.name = re.sub(r'^.*/(.*)', r'\1', disk_path)
    self.nvme_attributes = {}
    self.path = disk_path
    self.smart_attributes = {}
    self.smartctl = {}
    self.tests = OrderedDict()
    self.get_details()
    self.get_smart_details()

  def check_attributes(self, silent=False):
    """Check NVMe / SMART attributes for errors."""
    override_disabled = False
    if self.nvme_attributes:
      attr_type = 'NVMe'
      items = self.nvme_attributes.items()
    elif self.smart_attributes:
      attr_type = 'SMART'
      items = self.smar_attributes.items()
    for k, v in items:
      if k in ATTRIBUTES[attr_type]:
        if 'Error' not in ATTRIBUTES[attr_type][k]:
          # Only worried about error thresholds
          continue
        if ATTRIBUTES[attr_type][k].get('Ignore', False):
          # Attribute is non-failing, skip
          continue
        if v['raw'] >= ATTRIBUTES[attr_type][k]['Error']:
          self.disk_ok = False

          # Disable override if necessary
          override_disabled |= ATTRIBUTES[attr_type][k].get(
            'Critical', False)

    # SMART overall assessment
    ## NOTE: Only fail drives if the overall value exists and reports failed
    if not self.smartctl.get('smart_status', {}).get('passed', True):
      self.disk_ok = False
      override_disabled = True

    # Print errors
    if not silent:
      if self.disk_ok:
        # 199/C7 warning
        if self.smart_attributes.get(199, {}).get('raw', 0) > 0:
          print_warning('199/C7 error detected')
          print_standard('  (Have you tried swapping the disk cable?)')
      else:
        # Override?
        self.show_attributes()
        print_warning('{} error(s) detected.'.format(attr_type))
        if override_disabled:
          print_standard('Tests disabled for this device')
          pause()
        elif not (len(self.tests) == 3 and HW_OVERRIDES_LIMITED):
          self.disk_ok = HW_OVERRIDES_FORCED or ask(
            'Run tests on this device anyway?')

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
    for disk in [self.lsblk, *self.lsblk.get('children', [])]:
      self.labels.append(disk.get('label', ''))
      self.labels.append(disk.get('partlabel', ''))
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
        try:
          _id = int(a.get('id', -1))
        except ValueError:
          # Ignoring invalid attribute
          continue
        _name = str(a.get('name', 'UNKNOWN'))
        _raw = int(a.get('raw', {}).get('value', -1))
        _raw_str = a.get('raw', {}).get('string', 'UNKNOWN')

        # Fix power-on time
        _r = re.match(r'^(\d+)[Hh].*', _raw_str)
        if _id == 9 and _r:
          _raw = int(_r.group(1))

        # Add to dict
        self.smart_attributes[_id] = {
          'name': _name, 'raw': _raw, 'raw_str': _raw_str}

  def safety_check(self, silent=False):
    """Run safety checks and disable tests if necessary."""
    if self.nvme_attributes or self.smart_attributes:
      self.check_attributes(silent)
    else:
      # No NVMe/SMART details
      if silent:
        self.disk_ok = HW_OVERRIDES_FORCED
      else:
        print_warning(
          '  WARNING: No NVMe or SMART attributes available for: {}'.format(
            self.path))
        self.disk_ok = HW_OVERRIDES_FORCED or ask(
          'Run tests on this device anyway?')

    if not self.disk_ok:
      for t in ['badblocks', 'I/O Benchmark']:
        if t in self.tests:
          self.tests[t].disabled = True
          self.tests[t].update_status('Denied')

  def show_attributes(self):
    """Show NVMe/SMART attributes."""
    print_info('Device: {}'.format(self.path))
    print_standard(
      ' {size:>6} ({tran}) {model} {serial}'.format(**self.lsblk))
    print_info('Attributes')
    if self.nvme_attributes:
      for k, v in self.nvme_attributes.items():
        if k in ATTRIBUTES['NVMe']:
          print('TODO: {} {}'.format(k, v))
    elif self.smart_attributes:
      for k, v in self.smart_attributes.items():
        # TODO: If k == 199/C7 then append ' (bad cable?)' to line
        if k in ATTRIBUTES['SMART']:
          print('TODO: {} {}'.format(k, v))
      if not self.smartctl.get('smart_status', {}).get('passed', True):
        print_error('SMART overall self-assessment: Failed')
    else:
      print_warning('  No NVMe or SMART data available')

class State():
  """Object to track device objects and overall state."""
  def __init__(self):
    self.cpu = None
    self.disks = []
    self.panes = {}
    self.progress_out = '{}/progress.out'.format(global_vars['LogDir'])
    self.quick_mode = False
    self.tests = OrderedDict({
      'Prime95':  {
        'Enabled': False,
        'Function': run_mprime_test,
        'Objects': [],
        },
      'NVMe / SMART':     {
        'Enabled': False,
        'Function': run_nvme_smart_tests,
        'Objects': [],
        },
      'badblocks':        {
        'Enabled': False,
        'Function': run_badblocks_test,
        'Objects': [],
        },
      'I/O Benchmark':    {
        'Enabled': False,
        'Function': run_io_benchmark,
        'Objects': [],
        },
      })

  def init(self):
    """Remove test objects, set log, and add devices."""
    self.disks = []
    for k, v in self.tests.items():
      v['Objects'] = []

    # Update LogDir
    if not self.quick_mode:
      global_vars['LogDir'] = '{}/Logs/{}_{}'.format(
        global_vars['Env']['HOME'],
        get_ticket_number(),
        time.strftime('%Y-%m-%d_%H%M_%z'))
      os.makedirs(global_vars['LogDir'], exist_ok=True)
      global_vars['LogFile'] = '{}/Hardware Diagnostics.log'.format(
        global_vars['LogDir'])

    # Add CPU
    self.cpu = CpuObj()

    # Add block devices
    cmd = ['lsblk', '--json', '--nodeps', '--paths']
    result = run_program(cmd, check=False)
    json_data = json.loads(result.stdout.decode())
    for disk in json_data['blockdevices']:
      skip_disk = False
      disk_obj = DiskObj(disk['name'])

      # Skip loopback devices, optical devices, etc
      if disk_obj.lsblk['type'] != 'disk':
        skip_disk = True

      # Skip WK disks
      wk_label_regex = r'{}_(LINUX|UFD)'.format(KIT_NAME_SHORT)
      for label in disk_obj.labels:
        if re.search(wk_label_regex, label, re.IGNORECASE):
          skip_disk = True

      # Add disk
      if not skip_disk:
        self.disks.append(disk_obj)

class TestObj():
  """Object to track test data."""
  def __init__(self, dev, label=None, info_label=False):
    self.aborted = False
    self.dev = dev
    self.label = label
    self.info_label = info_label
    self.disabled = False
    self.failed = False
    self.passed = False
    self.report = []
    self.started = False
    self.status = ''
    self.update_status()

  def update_status(self, new_status=None):
    """Update status strings."""
    if self.disabled:
      return
    if new_status:
        self.status = build_status_string(
        self.label, new_status, self.info_label)
    elif not self.status:
        self.status = build_status_string(
        self.label, 'Pending', self.info_label)
    elif self.started and 'Pending' in self.status:
        self.status = build_status_string(
        self.label, 'Working', self.info_label)

# Functions
def build_outer_panes(state):
  """Build top and side panes."""
  clear_screen()

  # Top
  state.panes['Top'] = tmux_split_window(
    behind=True, lines=2, vertical=True,
    text=TOP_PANE_TEXT)

  # Started
  state.panes['Started'] = tmux_split_window(
    lines=SIDE_PANE_WIDTH, target_pane=state.panes['Top'],
    text='{BLUE}Started{CLEAR}\n{text}'.format(
      text=time.strftime("%Y-%m-%d %H:%M %Z"),
      **COLORS))

  # Progress
  state.panes['Progress'] = tmux_split_window(
    lines=SIDE_PANE_WIDTH,
    watch=state.progress_out)

def build_status_string(label, status, info_label=False):
  """Build status string with appropriate colors."""
  status_color = COLORS['CLEAR']
  if status in ['Denied', 'ERROR', 'NS', 'OVERRIDE']:
    status_color = COLORS['RED']
  elif status in ['Aborted', 'N/A', 'Skipped', 'Unknown', 'Working']:
    status_color = COLORS['YELLOW']
  elif status in ['CS']:
    status_color = COLORS['GREEN']

  return '{l_c}{l}{CLEAR}{s_c}{s:>{s_w}}{CLEAR}'.format(
    l_c=COLORS['BLUE'] if info_label else '',
    l=label,
    s_c=status_color,
    s=status,
    s_w=SIDE_PANE_WIDTH-len(label),
    **COLORS)

def check_disk_attributes(disk):
  """Check if disk should be tested and allow overrides."""
  needs_override = False
  print_standard('  {size:>6} ({tran}) {model} {serial}'.format(
    **disk.lsblk))

  # General checks
  if not disk.nvme_attributes and not disk.smart_attributes:
    needs_override = True
    print_warning(
      '  WARNING: No NVMe or SMART attributes available for: {}'.format(
      disk.path))

  # NVMe checks
  # TODO check all tracked attributes and set disk.failing if needed

  # SMART checks
  # TODO check all tracked attributes and set disk.failing if needed

  # Ask for override if necessary
  if needs_override:
    if ask('  Run tests on this device anyway?'):
      # TODO Set override for this disk
      pass
    else:
      for v in disk.tests.values():
        # Started is set to True to fix the status string
        v['Result'] = 'Skipped'
        v['Started'] = True
        v['Status'] = 'Skipped'
    print_standard('')

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
  elif s in ['Aborted', 'N/A', 'Unknown', 'Working', 'Skipped']:
    color = COLORS['YELLOW']
  elif s in ['CS']:
    color = COLORS['GREEN']
  return color

def menu_diags(state, args):
  """Main menu to select and run HW tests."""
  args = [a.lower() for a in args]
  title = '{}\nMain Menu'.format(TOP_PANE_TEXT)
  # NOTE: Changing the order of main_options will break everything
  main_options = [
    {'Base Name': 'Full Diagnostic', 'Enabled': False},
    {'Base Name': 'Disk Diagnostic', 'Enabled': False},
    {'Base Name': 'Disk Diagnostic (Quick)', 'Enabled': False},
    {'Base Name': 'Prime95', 'Enabled': False, 'CRLF': True},
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
      print('(FAKE) reboot...')
      sleep(1)
      # TODO uncomment below
      #run_program(['systemctl', 'reboot'])
    elif selection == 'P':
      print('(FAKE) poweroff...')
      sleep(1)
      # TODO uncomment below
      #run_program(['systemctl', 'poweroff'])
    elif selection == 'Q':
      break
    elif selection == 'S':
      run_hw_tests(state)

def run_audio_test():
  """Run audio test."""
  clear_screen()
  run_program(['hw-diags-audio'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')

def run_badblocks_test(state, test):
  """TODO"""
  tmux_update_pane(
    state.panes['Top'], text='{}\n{}'.format(
      TOP_PANE_TEXT, 'badblocks'))
  print_standard('TODO: run_badblocks_test({})'.format(
    test.dev.path))
  for disk in state.disks:
    disk.tests['badblocks']['Started'] = True
    update_progress_pane(state)
    sleep(3)
    disk.tests['badblocks']['Result'] = 'OVERRIDE'
    update_progress_pane(state)

def run_hw_tests(state):
  """Run enabled hardware tests."""
  print_standard('Scanning devices...')
  state.init()

  # Build Panes
  update_progress_pane(state)
  build_outer_panes(state)

  # Show selected tests and create TestObj()s
  print_info('Selected Tests:')
  for k, v in state.tests.items():
    print_standard('  {:<15} {}{}{} {}'.format(
      k,
      COLORS['GREEN'] if v['Enabled'] else COLORS['RED'],
      'Enabled' if v['Enabled'] else 'Disabled',
      COLORS['CLEAR'],
      QUICK_LABEL if state.quick_mode and 'NVMe' in k else ''))
    if v['Enabled']:
      # Create TestObj and track under both CpuObj/DiskObj and State
      if k in TESTS_CPU:
        test_obj = TestObj(
          dev=state.cpu, label='Prime95', info_label=True)
        state.cpu.tests[k] = test_obj
        v['Objects'].append(test_obj)
      elif k in TESTS_DISK:
        for disk in state.disks:
          test_obj = TestObj(dev=disk, label=disk.name)
          disk.tests[k] = test_obj
          v['Objects'].append(test_obj)
  print_standard('')

  # Run safety checks
  for disk in state.disks:
    disk.safety_check()

  # Run tests
  ## Because state.tests is an OrderedDict and the disks were added
  ##   in order, the tests will be run in order.
  for k, v in state.tests.items():
    if v['Enabled']:
      f = v['Function']
      for test_obj in v['Objects']:
        f(state, test_obj)

  # Done
  show_results(state)
  if '--quick' in sys.argv:
    pause('Press Enter to exit...')
  else:
    pause('Press Enter to return to main menu... ')

  # Cleanup
  tmux_kill_pane(*state.panes.values())

def run_io_benchmark(state, test):
  """TODO"""
  tmux_update_pane(
    state.panes['Top'], text='{}\n{}'.format(
      TOP_PANE_TEXT, 'I/O Benchmark'))
  print_standard('TODO: run_io_benchmark({})'.format(
    test.dev.path))
  for disk in state.disks:
    disk.tests['I/O Benchmark']['Started'] = True
    update_progress_pane(state)
    sleep(3)
    disk.tests['I/O Benchmark']['Result'] = 'Unknown'
    update_progress_pane(state)

def run_keyboard_test():
  """Run keyboard test."""
  clear_screen()
  run_program(['xev', '-event', 'keyboard'], check=False, pipe=False)

def run_mprime_test(state, test):
  """Test CPU with Prime95 and track temps."""
  test.started = True
  test.update_status()
  update_progress_pane(state)
  test.sensor_data = get_sensor_data()

  # Update top pane
  test.title = '{}\nPrime95: {}'.format(
    TOP_PANE_TEXT, test.dev.name)
  tmux_update_pane(state.panes['Top'], text=test.title)

  # Start live sensor monitor
  test.sensors_out = '{}/sensors.out'.format(global_vars['TmpDir'])
  with open(test.sensors_out, 'w') as f:
    f.write(' ')
    f.flush()
    sleep(0.5)
  test.monitor_proc = popen_program(
    ['hw-sensors-monitor', test.sensors_out],
    pipe=True)

  # Create monitor and worker panes
  state.panes['mprime'] = tmux_split_window(
    lines=10, vertical=True, text=' ')
  state.panes['Temps'] = tmux_split_window(
    behind=True, percent=80, vertical=True, watch=test.sensors_out)
  tmux_resize_pane(global_vars['Env']['TMUX_PANE'], y=3)

  # Get idle temps
  clear_screen()
  try_and_print(
    message='Getting idle temps...', indent=0,
    function=save_average_temp, cs='Done',
    sensor_data=test.sensor_data, temp_label='Idle',
    seconds=3)
  # TODO: Remove seconds kwarg above

  # Stress CPU
  print_log('Starting Prime95')
  test.abort_msg = 'If running too hot, press CTRL+c to abort the test'
  run_program(['apple-fans', 'max'])
  tmux_update_pane(
    state.panes['mprime'],
    command=['hw-diags-prime95', global_vars['TmpDir']],
    working_dir=global_vars['TmpDir'])
  #time_limit = int(MPRIME_LIMIT) * 60
  # TODO: restore above line
  time_limit = 10
  try:
    for i in range(time_limit):
      clear_screen()
      sec_left = (time_limit - i) % 60
      min_left = int( (time_limit - i) / 60)
      _status_str = 'Running Prime95 ('
      if min_left > 0:
        _status_str += '{} minute{}, '.format(
          min_left,
          's' if min_left != 1 else '')
      _status_str += '{} second{} left)'.format(
        sec_left,
        's' if sec_left != 1 else '')
      # Not using print wrappers to avoid flooding the log
      print(_status_str)
      print('{YELLOW}{msg}{CLEAR}'.format(msg=test.abort_msg, **COLORS))
      update_sensor_data(test.sensor_data)
      sleep(1)
  except KeyboardInterrupt:
    # Catch CTRL+C
    test.aborted = True
    test.update_status('Aborted')
    print_warning('\nAborted.')
    update_progress_pane(state)

    # Restart live monitor
    test.monitor_proc = popen_program(
      ['hw-sensors-monitor', test.sensors_out],
      pipe=True)

  # Stop Prime95 (twice for good measure)
  run_program(['killall', '-s', 'INT', 'mprime'], check=False)
  sleep(1)
  tmux_kill_pane(state.panes['mprime'])

  # Get cooldown temp
  run_program(['apple-fans', 'auto'])
  clear_screen()
  try_and_print(
    message='Letting CPU cooldown for bit...', indent=0,
    function=sleep, cs='Done', seconds=3)
  # TODO: Above seconds should be 10
  try_and_print(
    message='Getting cooldown temps...', indent=0,
    function=save_average_temp, cs='Done',
    sensor_data=test.sensor_data, temp_label='Cooldown',
    seconds=3)
  # TODO: Remove seconds kwarg above

  # Move logs to Ticket folder
  for item in os.scandir(global_vars['TmpDir']):
    try:
      shutil.move(item.path, global_vars['LogDir'])
    except Exception:
      print_error('ERROR: Failed to move "{}" to "{}"'.format(
        item.path,
        global_vars['LogDir']))

  # Check results and build report
  test.logs = {}
  for log in ['results.txt', 'prime.log']:
    lines = []
    log_path = '{}/{}'.format(global_vars['LogDir'], log)

    # Read and save log
    try:
      with open(log_path, 'r') as f:
        lines = f.read().splitlines()
      test.logs[log] = lines
    except FileNotFoundError:
      # Ignore since files may be missing for slower CPUs
      pass

    # results.txt (NS check)
    if log == 'results.txt':
      _tmp = []
      for line in lines:
        if re.search(r'(error|fail)', line, re.IGNORECASE):
          test.failed = True
          test.update_status('NS')
          _tmp.append('  {YELLOW}{line}{CLEAR}'.format(line=line, **COLORS))
      if _tmp:
        test.report.append('{BLUE}Log: results.txt{CLEAR}'.format(**COLORS))
        test.report.extend(_tmp)

    # prime.log (CS check)
    if log == 'prime.log':
      _tmp = {'Pass': {}, 'Warn': {}}
      for line in lines:
        _r = re.search(
          r'(completed.*(\d+) errors, (\d+) warnings)',
          line,
          re.IGNORECASE)
        if _r:
          if int(_r.group(2)) + int(_r.group(3)) > 0:
            # Encountered errors and/or warnings
            _tmp['Warn'][_r.group(1)] = None
          else:
            # No errors
            _tmp['Pass'][_r.group(1)] = None
      if len(_tmp['Warn']) > 0:
        # NS
        test.failed = True
        test.passed = False
        test.update_status('NS')
      elif len(_tmp['Pass']) > 0:
        test.passed = True
        test.update_status('CS')
      if len(_tmp['Pass']) + len(_tmp['Warn']) > 0:
        test.report.append('{BLUE}Log: prime.log{CLEAR}'.format(**COLORS))
        for line in sorted(_tmp['Pass'].keys()):
          test.report.append('  {}'.format(line))
        for line in sorted(_tmp['Warn'].keys()):
          test.report.append('  {YELLOW}{line}{CLEAR}'.format(line=line, **COLORS))

  # Finalize report
  if not (test.aborted or test.failed or test.passed):
    test.update_status('Unknown')
  test.report.append('{BLUE}Temps{CLEAR}'.format(**COLORS))
  for line in generate_report(
      test.sensor_data, 'Idle', 'Max', 'Cooldown', core_only=True):
    test.report.append('  {}'.format(line))

  # Done
  update_progress_pane(state)

  # Cleanup
  tmux_kill_pane(state.panes['mprime'], state.panes['Temps'])
  test.monitor_proc.kill()

def run_network_test():
  """Run network test."""
  clear_screen()
  run_program(['hw-diags-network'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')

def run_nvme_smart_tests(state, test):
  """Run NVMe or SMART test for test.dev."""
  tmux_update_pane(
    state.panes['Top'],
    text='{t}\nDisk Health: {size:>6} ({tran}) {model} {serial}'.format(
      t=TOP_PANE_TEXT, **test.dev.lsblk))
  if test.dev.nvme_attributes:
    # NOTE: Pass/Fail is just the attribute check
    if test.dev.disk_ok:
      test.passed = True
      test.update_status('CS')
    else:
      test.failed = True
      test.update_status('NS')
  elif test.dev.smart_attributes:
    if test.dev.disk_ok:
      test.passed = True
      test.update_status('CS')
    else:
      test.failed = True
      test.update_status('NS')
  else:
    print_standard('Tests disabled for this device')
    test.update_status('N/A')
    if not ask('Run tests on this device anyway?'):
      test.failed = True
    update_progress_pane(state)
  sleep(3)

def secret_screensaver(screensaver=None):
  """Show screensaver."""
  if screensaver == 'matrix':
    cmd = 'cmatrix -abs'.split()
  elif screensaver == 'pipes':
    cmd = 'pipes -t 0 -t 1 -t 2 -t 3 -p 5 -R -r 4000'.split()
  else:
    raise Exception('Invalid screensaver')
  run_program(cmd, check=False, pipe=False)

def show_results(state):
  """Show results for all tests."""
  clear_screen()
  tmux_update_pane(
    state.panes['Top'], text='{}\n{}'.format(
      TOP_PANE_TEXT, 'Results'))
  for k, v in state.tests.items():
    # Skip disabled tests
    if not v['Enabled']:
      continue
    print_success('{}:'.format(k))
    for obj in v['Objects']:
      for line in obj.report:
        print(line)
        print_log(strip_colors(line))
      print_standard(' ')
    if 'Prime95' not in k:
      print_standard(' ')

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

def update_progress_pane(state):
  """Update progress file for side pane."""
  output = []
  for k, v in state.tests.items():
    # Skip disabled sections
    if not v['Enabled']:
      continue

    # Add section name
    if k != 'Prime95':
      output.append('{BLUE}{name}{CLEAR}'.format(name=k, **COLORS))
    if 'SMART' in k and state.quick_mode:
      output[-1] += ' {}'.format(QUICK_LABEL)

    # Add status from test object(s)
    for test in v['Objects']:
      output.append(test.status)

    # Add spacer before next section
    output.append(' ')

  # Add line-endings
  output = ['{}\n'.format(line) for line in output]

  with open(state.progress_out, 'w') as f:
    f.writelines(output)

if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
