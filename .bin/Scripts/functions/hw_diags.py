# Wizard Kit: Functions - HW Diagnostics

import re
import time

from collections import OrderedDict
from functions.json import *
from functions.sensors import *
from functions.threading import *
from functions.tmux import *
from settings.hw_diags import *
if DEBUG_MODE:
  from debug.hw_diags import *


# Fix settings
OVERRIDES_FORCED = OVERRIDES_FORCED and not OVERRIDES_LIMITED
QUICK_LABEL = QUICK_LABEL.format(**COLORS)
TOP_PANE_TEXT = TOP_PANE_TEXT.format(**COLORS)


# Regex
REGEX_ERROR_STATUS = re.compile('|'.join(STATUSES['RED']))


# Error Classes
class DeviceTooSmallError(Exception):
  pass


# Classes
class CpuObj():
  """Object for tracking CPU specific data."""
  def __init__(self):
    self.lscpu = {}
    self.tests = OrderedDict()
    self.get_details()
    self.name = self.lscpu.get('Model name', 'Unknown CPU')
    self.description = self.name

  def get_details(self):
    """Get CPU details from lscpu."""
    cmd = ['lscpu', '--json']
    json_data = get_json_from_command(cmd)
    for line in json_data.get('lscpu', [{}]):
      _field = line.get('field', '').replace(':', '')
      _data = line.get('data', '')
      if not _field and not _data:
        # Skip
        print_warning(_field, _data)
        pause()
        continue
      self.lscpu[_field] = _data

  def generate_cpu_report(self):
    """Generate CPU report with data from all tests."""
    report = []
    report.append('{BLUE}Device{CLEAR}'.format(**COLORS))
    report.append('  {}'.format(self.name))

    # Include RAM details
    ram_details = get_ram_details()
    ram_total = human_readable_size(ram_details.pop('Total', 0)).strip()
    ram_dimms = ['{}x {}'.format(v, k) for k, v in sorted(ram_details.items())]
    report.append('{BLUE}RAM{CLEAR}'.format(**COLORS))
    report.append('  {} ({})'.format(ram_total, ', '.join(ram_dimms)))

    # Tests
    for test in self.tests.values():
      report.extend(test.report)

    return report


class DiskObj():
  """Object for tracking disk specific data."""
  def __init__(self, disk_path):
    self.attr_type = 'UNKNOWN'
    self.disk_ok = True
    self.labels = []
    self.lsblk = {}
    self.name = re.sub(r'^.*/(.*)', r'\1', disk_path)
    self.nvme_attributes = {}
    self.nvme_smart_notes = {}
    self.override_disabled = False
    self.path = disk_path
    self.smart_attributes = {}
    self.smart_self_test = {}
    self.smartctl = {}
    self.tests = OrderedDict()
    self.get_details()
    self.get_size()

    # Try enabling SMART
    run_program(
      cmd=[
        'sudo',
        'smartctl',
        '--tolerance=permissive',
        '--smart=on',
        self.path,
        ],
      check=False)

    # Get NVMe/SMART data and set description
    self.get_smart_details()
    self.description = '{size} ({tran}) {model} {serial}'.format(
      **self.lsblk)

  def add_nvme_smart_note(self, note):
    """Add note that will be included in the NVMe / SMART report."""
    # A dict is used to avoid duplicate notes
    self.nvme_smart_notes[note] = None

  def calc_io_dd_values(self):
    """Calcualte I/O benchmark dd values.

    Calculations
    The minimum dev size is 'Graph Horizontal Width' * 'Chunk Size'
      (e.g. 1.25 GB for a width of 40 and a chunk size of 32MB)
      If the device is smaller than the minimum dd_chunks would be set
      to zero which would cause a divide by zero error.
      If the device is below the minimum size an Exception will be raised

    dd_size is the area to be read in bytes
      If the dev is < 10Gb then it's the whole dev
      Otherwise it's the larger of 10Gb or 1% of the dev

    dd_chunks is the number of groups of "Chunk Size" in self.dd_size
      This number is reduced to a multiple of the graph width in
      order to allow for the data to be condensed cleanly

    dd_chunk_blocks is the chunk size in number of blocks
      (e.g. 64 if block size is 512KB and chunk size is 32MB

    dd_skip_blocks is the number of "Block Size" groups not tested
    dd_skip_count is the number of blocks to skip per self.dd_chunk
    dd_skip_extra is how often to add an additional skip block
      This is needed to ensure an even testing across the dev
      This is calculated by using the fractional amount left off
      of the dd_skip_count variable
    """
    self.dd_size = min(IO_VARS['Minimum Test Size'], self.size_bytes)
    self.dd_size = max(
      self.dd_size,
      self.size_bytes * IO_VARS['Alt Test Size Factor'])
    self.dd_chunks = int(self.dd_size // IO_VARS['Chunk Size'])
    self.dd_chunks -= self.dd_chunks % IO_VARS['Graph Horizontal Width']
    if self.dd_chunks < IO_VARS['Graph Horizontal Width']:
      raise DeviceTooSmallError
    self.dd_chunk_blocks = int(IO_VARS['Chunk Size'] / IO_VARS['Block Size'])
    self.dd_size = self.dd_chunks * IO_VARS['Chunk Size']
    self.dd_skip_blocks = int(
      (self.size_bytes - self.dd_size) // IO_VARS['Block Size'])
    self.dd_skip_count = int((self.dd_skip_blocks / self.dd_chunks) // 1)
    self.dd_skip_extra = 0
    try:
      self.dd_skip_extra = 1 + int(
        1 / ((self.dd_skip_blocks / self.dd_chunks) % 1))
    except ZeroDivisionError:
      # self.dd_skip_extra == 0 is fine
      pass

  def check_attributes(self):
    """Check NVMe / SMART attributes for errors, returns bool."""
    attr_type = self.attr_type
    disk_ok = True

    # Get updated attributes
    self.get_smart_details()

    # Check attributes
    if self.nvme_attributes:
      self.add_nvme_smart_note(
        '  {YELLOW}NVMe disk support is still experimental{CLEAR}'.format(
        **COLORS))
      items = self.nvme_attributes.items()
    elif self.smart_attributes:
      items = self.smart_attributes.items()
    for k, v in items:
      if k in ATTRIBUTES[attr_type]:
        if not ATTRIBUTES[attr_type][k]['Error']:
          # Informational attribute, skip
          continue
        if ATTRIBUTES[attr_type][k]['Ignore']:
          # Attribute is non-failing, skip
          continue
        if v['raw'] >= ATTRIBUTES[attr_type][k]['Error']:
          if (ATTRIBUTES[attr_type][k]['Maximum']
              and v['raw'] >= ATTRIBUTES[attr_type][k]['Maximum']):
            # Non-standard value, skip
            continue
          else:
            disk_ok = False

            # Disable override if necessary
            if ATTRIBUTES[attr_type][k].get('Critical', False):
              self.override_disabled = True

    # SMART overall assessment
    ## NOTE: Only fail drives if the overall value exists and reports failed
    if not self.smartctl.get('smart_status', {}).get('passed', True):
      disk_ok = False
      self.override_disabled = True
      self.add_nvme_smart_note(
        '  {RED}SMART overall self-assessment: Failed{CLEAR}'.format(**COLORS))

    # Done
    return disk_ok

  def check_smart_self_test(self, silent=False):
    """Check if a SMART self-test is currently running, returns bool."""
    msg = 'SMART self-test in progress'
    test_running = 'remaining_percent' in self.smart_self_test.get('status', '')

    if test_running:
      # Ask to abort
      if not silent:
        print_warning('WARNING: {}'.format(msg))
        print_standard(' ')
        if ask('Abort HW Diagnostics?'):
          raise GenericAbort('Bail')

      # Add warning note
      self.add_nvme_smart_note(
        '  {YELLOW}WARNING: {msg}{CLEAR}'.format(msg=msg, **COLORS))

    # Done
    return test_running

  def disable_test(self, name, status, test_failed=False):
    """Disable test by name and update status."""
    if name in self.tests:
      self.tests[name].update_status(status)
      self.tests[name].disabled = True
      self.tests[name].failed = test_failed

  def generate_attribute_report(
      self, description=False, timestamp=False):
    """Generate NVMe / SMART report, returns list."""
    attr_type = self.attr_type
    report = []
    if description:
      report.append('{BLUE}Device ({name}){CLEAR}'.format(
        name=self.name, **COLORS))
      report.append('  {}'.format(self.description))

    # Skip attributes if they don't exist
    if not (self.nvme_attributes or self.smart_attributes):
      report.append(
        '  {YELLOW}No NVMe or SMART data available{CLEAR}'.format(
          **COLORS))
      return report

    # Attributes
    report.append('{BLUE}{a} Attributes{YELLOW}{u:>23} {t}{CLEAR}'.format(
      a=attr_type,
      u='Updated:' if timestamp else '',
      t=time.strftime('%Y-%m-%d %H:%M %Z') if timestamp else '',
      **COLORS))
    if self.nvme_attributes:
      attr_type = 'NVMe'
      items = self.nvme_attributes.items()
    elif self.smart_attributes:
      attr_type = 'SMART'
      items = self.smart_attributes.items()
    for k, v in items:
      if k in ATTRIBUTES[attr_type]:
        _note = ''
        _color = COLORS['GREEN']

        # Attribute ID & Name
        if attr_type == 'NVMe':
          _line = '  {:38}'.format(k.replace('_', ' ').title())
        else:
          _line = '  {i:>3} / {h}: {n:28}'.format(
            i=k,
            h=ATTRIBUTES[attr_type][k]['Hex'],
            n=v['name'][:28])

        # Set color
        for _t, _c in ATTRIBUTE_COLORS:
          if ATTRIBUTES[attr_type][k][_t]:
            if v['raw'] >= ATTRIBUTES[attr_type][k][_t]:
              _color = COLORS[_c]
              if _t == 'Maximum':
                _note = '(invalid?)'

        # 199/C7 warning
        if str(k) == '199' and v['raw'] > 0:
          _note = '(bad cable?)'

        # Attribute value
        _line += '{c}{v} {YELLOW}{n}{CLEAR}'.format(
          c=_color,
          v=v['raw_str'],
          n=_note,
          **COLORS)

        # Add line to report
        report.append(_line)

    # Done
    return report

  def generate_disk_report(self):
    """Generate disk report with data from all tests."""
    report = []

    # Attributes
    report.extend(self.generate_attribute_report(description=True))

    # Notes
    if self.nvme_smart_notes:
      report.append('{BLUE}{attr_type} Notes{CLEAR}'.format(
        attr_type=self.attr_type, **COLORS))
      report.extend(sorted(self.nvme_smart_notes.keys()))

    # 4K alignment check
    if not self.is_4k_aligned():
      report.append('{YELLOW}Warning{CLEAR}'.format(**COLORS))
      report.append('  One or more partitions are not 4K aligned')

    # Tests
    for test in self.tests.values():
      report.extend(test.report)

    return report

  def get_details(self):
    """Get data from lsblk."""
    cmd = ['lsblk', '--json', '--output-all', '--paths', self.path]
    json_data = get_json_from_command(cmd)
    self.lsblk = json_data.get('blockdevices', [{}])[0]

    # Set necessary details
    self.lsblk['model'] = self.lsblk.get('model', 'Unknown Model')
    self.lsblk['name'] = self.lsblk.get('name', self.path)
    self.lsblk['phy-sec'] = self.lsblk.get('phy-sec', -1)
    self.lsblk['rota'] = self.lsblk.get('rota', True)
    self.lsblk['serial'] = self.lsblk.get('serial', 'Unknown Serial')
    self.lsblk['size'] = self.lsblk.get('size', '???b')
    self.lsblk['tran'] = self.lsblk.get('tran', '???')

    # Ensure certain attributes types
    for attr in ['model', 'name', 'rota', 'serial', 'size', 'tran']:
      if not isinstance(self.lsblk[attr], str):
        self.lsblk[attr] = str(self.lsblk[attr])
    for attr in ['phy-sec']:
      if not isinstance(self.lsblk[attr], int):
        self.lsblk[attr] = int(self.lsblk[attr])
    self.lsblk['tran'] = self.lsblk['tran'].upper().replace('NVME', 'NVMe')

    # Build list of labels
    for disk in [self.lsblk, *self.lsblk.get('children', [])]:
      self.labels.append(disk.get('label', ''))
      self.labels.append(disk.get('partlabel', ''))
    self.labels = [str(label) for label in self.labels if label]

  def get_size(self):
    """Get real disk size."""
    cmd = ['lsblk',
      '--bytes', '--nodeps', '--noheadings',
      '--output', 'size', self.path]
    try:
      result = run_program(cmd)
      self.size_bytes = int(result.stdout.decode().strip())
    except Exception:
      # Setting to impossible value for now
      self.size_bytes = -1

  def get_smart_details(self):
    """Get data from smartctl."""
    cmd = [
      'sudo',
      'smartctl',
      '--tolerance=verypermissive',
      '--all',
      '--json',
      self.path,
      ]
    self.smartctl = get_json_from_command(cmd, check=False)

    # Check for attributes
    if KEY_NVME in self.smartctl:
      self.attr_type = 'NVMe'
      self.nvme_attributes = {}
      for k, v in self.smartctl[KEY_NVME].items():
        try:
          self.nvme_attributes[k] = {
            'name': k,
            'raw': int(v),
            'raw_str': str(v),
            }
        except Exception:
          # TODO: Limit this check
          pass
    elif KEY_SMART in self.smartctl:
      self.attr_type = 'SMART'
      for a in self.smartctl[KEY_SMART].get('table', {}):
        try:
          _id = int(a.get('id', -1))
        except ValueError:
          # Ignoring invalid attribute
          continue
        _name = str(a.get('name', 'UNKNOWN')).replace('_', ' ').title()
        _raw = int(a.get('raw', {}).get('value', -1))
        _raw_str = a.get('raw', {}).get('string', 'UNKNOWN')

        # Fix power-on time
        _r = re.match(r'^(\d+)[Hh].*', _raw_str)
        if _id == 9 and _r:
          _raw = int(_r.group(1))

        # Add to dict
        self.smart_attributes[_id] = {
          'name': _name, 'raw': _raw, 'raw_str': _raw_str}

      # Self-test data
      self.smart_self_test = {}
      for k in ['polling_minutes', 'status']:
        self.smart_self_test[k] = self.smartctl.get(
            'ata_smart_data', {}).get(
            'self_test', {}).get(
            k, {})

  def is_4k_aligned(self):
    """Check if partitions are 4K aligned, returns bool."""
    cmd = [
      'sudo',
      'sfdisk',
      '--json',
      self.path,
      ]
    aligned = True

    # Get partition details
    json_data = get_json_from_command(cmd)

    # Check partitions
    for part in json_data.get('partitiontable', {}).get('partitions', []):
      aligned = aligned and part.get('start', -1) % 4096 == 0

    # Done
    return aligned

  def safety_check(self, silent=False):
    """Run safety checks and disable tests if necessary."""
    test_running = False
    if self.nvme_attributes or self.smart_attributes:
      disk_ok = self.check_attributes()
      test_running = self.check_smart_self_test(silent)

      # Show errors (unless a SMART self-test is running)
      if not (silent or test_running):
        if disk_ok:
          # 199/C7 warning
          if self.smart_attributes.get(199, {}).get('raw', 0) > 0:
            print_warning('199/C7 error detected')
            print_standard('  (Have you tried swapping the disk cable?)')
        else:
          # Override?
          show_report(
            self.generate_attribute_report(description=True),
            log_report=True)
          print_warning('  {} error(s) detected.'.format(self.attr_type))
          if self.override_disabled:
            print_standard('Tests disabled for this device')
            pause()
          elif not (len(self.tests) == 3 and OVERRIDES_LIMITED):
            if OVERRIDES_FORCED or ask('Run tests on this device anyway?'):
              disk_ok = True
              if 'NVMe / SMART' in self.tests:
                self.disable_test('NVMe / SMART', 'OVERRIDE')
                if not self.nvme_attributes and self.smart_attributes:
                  # Re-enable for SMART short-tests
                  self.tests['NVMe / SMART'].disabled = False
              print_standard(' ')
    else:
      # No NVMe/SMART details
      self.disable_test('NVMe / SMART', 'N/A')
      if silent:
        disk_ok = OVERRIDES_FORCED
      else:
        show_report(
          self.generate_attribute_report(description=True),
          log_report=True)
        disk_ok = OVERRIDES_FORCED or ask('Run tests on this device anyway?')
        print_standard(' ')

    # Disable tests if necessary (statuses won't be overwritten)
    if test_running:
      if not silent:
        # silent is only True in quick_mode
        self.disable_test('NVMe / SMART', 'Denied')
      for t in ['badblocks', 'I/O Benchmark']:
        self.disable_test(t, 'Denied')
    elif not disk_ok:
      self.disable_test('NVMe / SMART', 'NS', test_failed=True)
      for t in ['badblocks', 'I/O Benchmark']:
        self.disable_test(t, 'Denied')


class State():
  """Object to track device objects and overall state."""
  def __init__(self):
    self.args = None
    self.cpu = None
    self.disks = []
    self.panes = {}
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

  def build_outer_panes(self):
    """Build top and side panes."""
    clear_screen()

    # Top
    self.panes['Top'] = tmux_split_window(
      behind=True, lines=2, vertical=True,
      text=TOP_PANE_TEXT)

    # Started
    self.panes['Started'] = tmux_split_window(
      lines=SIDE_PANE_WIDTH, target_pane=self.panes['Top'],
      text='{BLUE}Started{CLEAR}\n{s}'.format(
        s=time.strftime("%Y-%m-%d %H:%M %Z"),
        **COLORS))

    # Progress
    self.panes['Progress'] = tmux_split_window(
      lines=SIDE_PANE_WIDTH,
      watch=self.progress_out)

  def fix_tmux_panes(self):
    """Fix pane sizes if the window has been resized."""
    needs_fixed = False

    # Bail?
    if not self.panes:
      return

    # Check layout
    for k, v in self.tmux_layout.items():
      if not  v.get('Check'):
        # Not concerned with the size of this pane
        continue
      # Get target
      target = None
      if k != 'Current':
        if k not in self.panes:
          # Skip missing panes
          continue
        else:
          target = self.panes[k]

      # Check pane size
      x, y = tmux_get_pane_size(pane_id=target)
      if v.get('x', False) and v['x'] != x:
        needs_fixed = True
      if v.get('y', False) and v['y'] != y:
        needs_fixed = True

    # Bail?
    if not needs_fixed:
      return

    # Update layout
    for k, v in self.tmux_layout.items():
      # Get target
      target = None
      if k != 'Current':
        if k not in self.panes:
          # Skip missing panes
          continue
        else:
          target = self.panes[k]

      # Resize pane
      tmux_resize_pane(pane_id=target, **v)

  def fix_tmux_panes_loop(self):
    while True:
      try:
        self.fix_tmux_panes()
        sleep(1)
      except RuntimeError:
        # Assuming layout definitions changes mid-run, ignoring
        pass

  def init(self):
    """Remove test objects, set log, and add devices."""
    self.disks = []
    for k, v in self.tests.items():
      v['Objects'] = []

    # Update LogDir
    if self.quick_mode:
      global_vars['LogDir'] = '{}/Logs/{}'.format(
        global_vars['Env']['HOME'],
        time.strftime('%Y-%m-%d_%H%M_%z'))
    else:
      global_vars['LogDir'] = '{}/Logs/{}_{}'.format(
        global_vars['Env']['HOME'],
        get_ticket_number(),
        time.strftime('%Y-%m-%d_%H%M_%z'))
    os.makedirs(global_vars['LogDir'], exist_ok=True)
    global_vars['LogFile'] = '{}/Hardware Diagnostics.log'.format(
      global_vars['LogDir'])
    self.progress_out = '{}/progress.out'.format(global_vars['LogDir'])

    # Add CPU
    self.cpu = CpuObj()

    # Add block devices
    cmd = ['lsblk', '--json', '--nodeps', '--paths']
    json_data = get_json_from_command(cmd)
    for disk in json_data.get('blockdevices', []):
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

    # Start tmux thread
    self.tmux_layout = TMUX_LAYOUT.copy()
    start_thread(self.fix_tmux_panes_loop)

  def set_top_pane_text(self, text):
    """Set top pane text using TOP_PANE_TEXT and provided text."""
    tmux_update_pane(
      self.panes['Top'],
      text='{}\n{}'.format(TOP_PANE_TEXT, text))


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
    if self.disabled or REGEX_ERROR_STATUS.search(self.status):
      # Don't update error statuses if test is enabled
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
def build_status_string(label, status, info_label=False):
  """Build status string with appropriate colors."""
  status_color = COLORS['CLEAR']
  for k, v in STATUSES.items():
    if status in v:
      status_color = COLORS[k]

  return '{l_c}{l}{CLEAR}{s_c}{s:>{s_w}}{CLEAR}'.format(
    l_c=COLORS['BLUE'] if info_label else '',
    l=label,
    s_c=status_color,
    s=status,
    s_w=SIDE_PANE_WIDTH-len(label),
    **COLORS)


def generate_horizontal_graph(rates, oneline=False):
  """Generate horizontal graph from rates, returns list."""
  graph = ['', '', '', '']
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
      graph[0] += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-24])
      graph[1] += full_block
      graph[2] += full_block
      graph[3] += full_block
    elif step >= 16:
      graph[0] += ' '
      graph[1] += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-16])
      graph[2] += full_block
      graph[3] += full_block
    elif step >= 8:
      graph[0] += ' '
      graph[1] += ' '
      graph[2] += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step-8])
      graph[3] += full_block
    else:
      graph[0] += ' '
      graph[1] += ' '
      graph[2] += ' '
      graph[3] += '{}{}'.format(r_color, IO_VARS['Graph Horizontal'][step])
  graph = [line+COLORS['CLEAR'] for line in graph]
  if oneline:
    return graph[:-1]
  else:
    return graph


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


def get_ram_details():
  """Get RAM details via dmidecode, returns dict."""
  cmd = ['sudo', 'dmidecode', '--type', 'memory']
  manufacturer = 'UNKNOWN'
  ram_details = {'Total': 0}
  size = 0

  # Get DMI data
  result = run_program(cmd, encoding='utf-8', errors='ignore')
  dmi_data = result.stdout.splitlines()

  # Parse data
  for line in dmi_data:
    line = line.strip()
    if line == 'Memory Device':
      # Reset vars
      manufacturer = 'UNKNOWN'
      size = 0
    elif line.startswith('Size:'):
      size = convert_to_bytes(line.replace('Size: ', ''))
    elif line.startswith('Manufacturer:'):
      manufacturer = line.replace('Manufacturer: ', '')
      if size > 0:
        # Add RAM to list if slot populated
        ram_str = '{} {}'.format(
          human_readable_size(size).strip(),
          manufacturer,
          )
        ram_details['Total'] += size
        if ram_str in ram_details:
          ram_details[ram_str] += 1
        else:
          ram_details[ram_str] = 1

  # Done
  return ram_details


def get_read_rate(s):
  """Get read rate in bytes/s from dd progress output."""
  real_rate = None
  if re.search(r'[KMGT]B/s', s):
    human_rate = re.sub(r'^.*\s+(\d+\.?\d*)\s+(.B)/s\s*$', r'\1 \2', s)
    real_rate = convert_to_bytes(human_rate)
  return real_rate


def menu_diags(state, args):
  """Main menu to select and run HW tests."""
  args = [a.lower() for a in args]
  state.args = args
  checkmark = '*'
  if 'DISPLAY' in global_vars['Env']:
    checkmark = '✓'
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
        state.quick_mode = state.quick_mode and not opt['Enabled']
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
      opt['Name'] = '[{}] {} {}'.format(
        checkmark if opt['Enabled'] else ' ',
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
      run_program(['/usr/local/bin/wk-power-command', 'reboot'])
    elif selection == 'P':
      run_program(['/usr/local/bin/wk-power-command', 'poweroff'])
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
  """Run a read-only surface scan with badblocks."""
  dev = test.dev

  # Bail early
  if test.disabled:
    return

  def _save_badblocks_output(read_all=False, timeout=0.1):
    """Get badblocks output and append to both file and var."""
    _output = ''
    while _output is not None:
      _output = test.badblocks_nbsr.read(0.1)
      if _output is not None:
        test.badblocks_stderr += _output.decode()
        with open(test.badblocks_out, 'a') as f:
          f.write(_output.decode())
      if not read_all:
        break

  # Prep
  print_log('Starting badblocks test for {}'.format(dev.path))
  test.started = True
  test.update_status()
  update_progress_pane(state)

  # Update tmux layout
  state.set_top_pane_text(dev.description)

  # Create monitor pane
  test.badblocks_out = '{}/badblocks_{}.out'.format(
    global_vars['LogDir'], dev.name)
  state.panes['badblocks'] = tmux_split_window(
    lines=5, vertical=True, watch=test.badblocks_out, watch_cmd='tail')

  # Show disk details
  clear_screen()
  show_report(dev.generate_attribute_report())
  print_standard(' ')

  # Set read block size
  if dev.lsblk['phy-sec'] == 4096 or dev.size_bytes >= BADBLOCKS_LARGE_DISK:
    block_size = '4096'
  else:
    # Use default value
    block_size = '1024'

  # Start badblocks
  print_standard('Running badblocks test...')
  test.badblocks_proc = popen_program(
    ['sudo', 'badblocks', '-sv', '-b', block_size, '-e', '1', dev.path],
    pipe=True, bufsize=1)
  test.badblocks_nbsr = NonBlockingStreamReader(test.badblocks_proc.stderr)
  test.badblocks_stderr = ''

  # Update progress loop
  try:
    while test.badblocks_proc.poll() is None:
      _save_badblocks_output()
  except KeyboardInterrupt:
    run_program(['killall', 'badblocks'], check=False)
    test.aborted = True

  # Save remaining badblocks output
  _save_badblocks_output(read_all=True)

  # Check result and build report
  test.report.append('{BLUE}badblocks{CLEAR}'.format(**COLORS))
  for line in test.badblocks_stderr.splitlines():
    line = line.strip()
    if not line or re.search(r'^Checking', line, re.IGNORECASE):
      # Skip empty and progress lines
      continue
    if re.search(r'^Pass completed.*0.*0/0/0', line, re.IGNORECASE):
      test.report.append('  {}'.format(line))
      if not test.aborted:
        test.passed = True
    else:
      test.report.append('  {YELLOW}{line}{CLEAR}'.format(
        line=line, **COLORS))
      if not test.aborted:
        test.failed = True
  if test.aborted:
    test.report.append('  {YELLOW}Aborted{CLEAR}'.format(**COLORS))
    test.update_status('Aborted')
    raise GenericAbort('Aborted')

  # Disable other drive tests if necessary
  if not test.passed:
    dev.disable_test('I/O Benchmark', 'Denied')

  # Update status
  if test.failed:
    test.update_status('NS')
  elif test.passed:
    test.update_status('CS')
  else:
    test.update_status('Unknown')

  # Done
  update_progress_pane(state)

  # Cleanup
  tmux_kill_pane(state.panes.pop('badblocks', None))


def run_hw_tests(state):
  """Run enabled hardware tests."""
  print_standard('Scanning devices...')
  state.init()
  tests_enabled = False

  # Build Panes
  update_progress_pane(state)
  state.build_outer_panes()

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
      tests_enabled = True

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

  # Bail if no tests selected
  if not tests_enabled:
    tmux_kill_pane(*state.panes.values())
    return

  # Run disk safety checks (if necessary)
  _disk_tests_enabled = False
  for k in TESTS_DISK:
    if state.tests[k]['Enabled']:
      _disk_tests_enabled = True
  if _disk_tests_enabled:
    for disk in state.disks:
      try:
        disk.safety_check(silent=state.quick_mode)
      except GenericAbort:
        tmux_kill_pane(*state.panes.values())
        state.panes.clear()
        return

  # Run tests
  ## Because state.tests is an OrderedDict and the disks were added
  ##   in order, the tests will be run in order.
  try:
    for k, v in state.tests.items():
      if v['Enabled']:
        f = v['Function']
        for test_obj in v['Objects']:
          f(state, test_obj)
        if not v['Objects']:
          # No devices available
          v['Objects'].append(TestObj(dev=None, label=''))
          v['Objects'][-1].update_status('N/A')
    # Recheck attributes
    if state.tests['NVMe / SMART']['Enabled']:
      for test_obj in state.tests['NVMe / SMART']['Objects']:
        if test_obj.dev is not None:
          # dev == None for the 'N/A' lines set above
          run_nvme_smart_tests(state, test_obj, update_mode=True)

  except GenericAbort:
    # Cleanup
    tmux_kill_pane(*state.panes.values())
    state.panes.clear()
    state.tmux_layout.pop('Current', None)

    # Rebuild panes
    update_progress_pane(state)
    state.build_outer_panes()

    # Mark unfinished tests as aborted
    for k, v in state.tests.items():
      if v['Enabled']:
        for test_obj in v['Objects']:
          if re.search(r'(Pending|Working)', test_obj.status):
            test_obj.update_status('Aborted')

    # Update side pane
    update_progress_pane(state)

  # Show results
  show_results(state)

  # Upload for review
  if ENABLED_UPLOAD_DATA and ask('Upload results for review?'):
    try_and_print(
      message='Saving debug reports...',
      function=save_debug_reports,
      state=state, global_vars=global_vars)
    try_and_print(
      message='Uploading Data...',
      function=upload_logdir,
      global_vars=global_vars,
      reason='Review')

  # Done
  sleep(1)
  if state.quick_mode:
    pause('Press Enter to exit... ')
  else:
    pause('Press Enter to return to main menu... ')

  # Cleanup
  tmux_kill_pane(*state.panes.values())
  state.panes.clear()


def run_io_benchmark(state, test):
  """Run a read-only I/O benchmark using dd."""
  dev = test.dev

  # Bail early
  if test.disabled:
    return

  # Prep
  print_log('Starting I/O benchmark test for {}'.format(dev.path))
  test.started = True
  test.update_status()
  update_progress_pane(state)

  # Update tmux layout
  state.set_top_pane_text(dev.description)
  state.tmux_layout['Current'] = {'y': 15, 'Check': True}

  # Create monitor pane
  test.io_benchmark_out = '{}/io_benchmark_{}.out'.format(
    global_vars['LogDir'], dev.name)
  state.panes['io_benchmark'] = tmux_split_window(
    percent=75, vertical=True,
    watch=test.io_benchmark_out, watch_cmd='tail')
  tmux_resize_pane(y=15)

  # Show disk details
  clear_screen()
  show_report(dev.generate_attribute_report())
  print_standard(' ')

  # Start I/O Benchmark
  print_standard('Running I/O benchmark test...')
  try:
    test.merged_rates = []
    test.read_rates = []
    dev.calc_io_dd_values()

    # Run dd read tests
    offset = 0
    for i in range(dev.dd_chunks):
      # Build cmd
      i += 1
      skip = dev.dd_skip_count
      if dev.dd_skip_extra and i % dev.dd_skip_extra == 0:
        skip += 1
      cmd = [
        'sudo', 'dd',
        'bs={}'.format(IO_VARS['Block Size']),
        'skip={}'.format(offset+skip),
        'count={}'.format(dev.dd_chunk_blocks),
        'iflag=direct',
        'if={}'.format(dev.path),
        'of=/dev/null']

      # Run cmd and get read rate
      result = run_program(cmd)
      result_str = result.stderr.decode().replace('\n', '')
      cur_rate = get_read_rate(result_str)

      # Add rate to lists
      test.read_rates.append(cur_rate)

      # Show progress
      if i % IO_VARS['Progress Refresh Rate'] == 0:
        update_io_progress(
          percent=(i/dev.dd_chunks)*100,
          rate=cur_rate,
          progress_file=test.io_benchmark_out)

      # Update offset
      offset += dev.dd_chunk_blocks + skip

  except DeviceTooSmallError:
    # Device too small, skipping test
    test.update_status('N/A')
  except KeyboardInterrupt:
    test.aborted = True
  except (subprocess.CalledProcessError, TypeError, ValueError):
    # Something went wrong, results unknown
    test.update_status('ERROR')

  # Check result and build report
  test.report.append('{BLUE}I/O Benchmark{CLEAR}'.format(**COLORS))
  if test.aborted:
    test.report.append('  {YELLOW}Aborted{CLEAR}'.format(**COLORS))
    raise GenericAbort('Aborted')
  elif not test.read_rates:
    if 'ERROR' in test.status:
      test.report.append('  {RED}Unknown error{CLEAR}'.format(**COLORS))
    elif 'N/A' in test.status:
      # Device too small
      test.report.append('  {YELLOW}Disk too small to test{CLEAR}'.format(
        **COLORS))
  else:
    # Merge rates for horizontal graph
    offset = 0
    width = int(dev.dd_chunks / IO_VARS['Graph Horizontal Width'])
    for i in range(IO_VARS['Graph Horizontal Width']):
      test.merged_rates.append(
        sum(test.read_rates[offset:offset+width])/width)
      offset += width

    # Add horizontal graph to report
    for line in generate_horizontal_graph(test.merged_rates):
      if not re.match(r'^\s+$', strip_colors(line)):
        test.report.append(line)

    # Add read speeds to report
    avg_read = sum(test.read_rates) / len(test.read_rates)
    min_read = min(test.read_rates)
    max_read = max(test.read_rates)
    avg_min_max = 'Read speeds    avg: {:3.1f}'.format(avg_read/(1024**2))
    avg_min_max += ' min: {:3.1f}'.format(min_read/(1024**2))
    avg_min_max += ' max: {:3.1f}'.format(max_read/(1024**2))
    test.report.append(avg_min_max)

    # Compare read speeds to thresholds
    if dev.lsblk['rota']:
      # Use HDD scale
      thresh_min = IO_VARS['Threshold HDD Min']
      thresh_high_avg = IO_VARS['Threshold HDD High Avg']
      thresh_low_avg = IO_VARS['Threshold HDD Low Avg']
    else:
      # Use SSD scale
      thresh_min = IO_VARS['Threshold SSD Min']
      thresh_high_avg = IO_VARS['Threshold SSD High Avg']
      thresh_low_avg = IO_VARS['Threshold SSD Low Avg']
    if min_read <= thresh_min and avg_read <= thresh_high_avg:
      test.failed = True
    elif avg_read <= thresh_low_avg:
      test.failed = True
    else:
      test.passed = True

  # Update status
  if test.failed:
    test.update_status('NS')
  elif test.passed:
    test.update_status('CS')
  elif not 'N/A' in test.status:
    test.update_status('Unknown')

  # Done
  update_progress_pane(state)

  # Cleanup
  state.tmux_layout.pop('Current', None)
  tmux_kill_pane(state.panes.pop('io_benchmark', None))


def run_keyboard_test():
  """Run keyboard test."""
  clear_screen()
  run_program(['xev', '-event', 'keyboard'], check=False, pipe=False)


def run_mprime_test(state, test):
  """Test CPU with Prime95 and track temps."""
  dev = test.dev

  # Bail early
  if test.disabled:
    return

  # Prep
  print_log('Starting Prime95 test')
  test.started = True
  test.update_status()
  update_progress_pane(state)
  test.sensor_data = get_sensor_data()
  test.thermal_abort = False

  # Update tmux layout
  state.set_top_pane_text(dev.name)

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
  state.panes['Prime95'] = tmux_split_window(
    lines=10, vertical=True, text=' ')
  state.panes['Temps'] = tmux_split_window(
    behind=True, percent=80, vertical=True, watch=test.sensors_out)
  tmux_resize_pane(global_vars['Env']['TMUX_PANE'], y=3)
  state.tmux_layout['Current'] = {'y': 3, 'Check': True}

  # Get idle temps
  clear_screen()
  try_and_print(
    message='Getting idle temps...', indent=0,
    function=save_average_temp, cs='Done',
    sensor_data=test.sensor_data, temp_label='Idle',
    seconds=5)

  # Stress CPU
  print_log('Starting Prime95')
  test.abort_msg = 'If running too hot, press CTRL+c to abort the test'
  run_program(['apple-fans', 'max'], check=False)
  tmux_update_pane(
    state.panes['Prime95'],
    command=['hw-diags-prime95', global_vars['TmpDir']],
    working_dir=global_vars['TmpDir'])
  time_limit = MPRIME_LIMIT * 60
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
      update_sensor_data(test.sensor_data, THERMAL_LIMIT)

      # Wait
      sleep(1)
  except (KeyboardInterrupt, ThermalLimitReachedError) as err:
    # CTRL+c pressed or thermal limit reached
    test.aborted = True
    if isinstance(err, KeyboardInterrupt):
      test.update_status('Aborted')
    elif isinstance(err, ThermalLimitReachedError):
      test.failed = True
      test.thermal_abort = True
      test.update_status('NS')
    update_progress_pane(state)

    # Restart live monitor
    test.monitor_proc = popen_program(
      ['hw-sensors-monitor', test.sensors_out],
      pipe=True)

  # Stop Prime95 (twice for good measure)
  run_program(['killall', '-s', 'INT', 'mprime'], check=False)
  sleep(1)
  tmux_kill_pane(state.panes.pop('Prime95', None))

  # Get cooldown temp
  run_program(['apple-fans', 'auto'], check=False)
  clear_screen()
  try_and_print(
    message='Letting CPU cooldown for bit...', indent=0,
    function=sleep, cs='Done', seconds=10)
  try_and_print(
    message='Getting cooldown temps...', indent=0,
    function=save_average_temp, cs='Done',
    sensor_data=test.sensor_data, temp_label='Cooldown',
    seconds=5)

  # Move logs to Ticket folder
  for item in os.scandir(global_vars['TmpDir']):
    try:
      shutil.move(item.path, global_vars['LogDir'])
    except Exception:
      print_error('ERROR: Failed to move "{}" to "{}"'.format(
        item.path,
        global_vars['LogDir']))

  # Check results and build report
  test.report.append('{BLUE}Prime95{CLEAR}'.format(**COLORS))
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
      for line in lines:
        line = line.strip()
        if re.search(r'(error|fail)', line, re.IGNORECASE):
          test.failed = True
          test.update_status('NS')
          test.report.append(
            '  {YELLOW}{line}{CLEAR}'.format(line=line, **COLORS))

    # prime.log (CS check)
    if log == 'prime.log':
      _tmp = {'Pass': {}, 'Warn': {}}
      for line in lines:
        line = line.strip()
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
      elif len(_tmp['Pass']) > 0 and not test.aborted:
        test.passed = True
        test.update_status('CS')
      for line in sorted(_tmp['Pass'].keys()):
        test.report.append('  {}'.format(line))
      for line in sorted(_tmp['Warn'].keys()):
        test.report.append(
          '  {YELLOW}{line}{CLEAR}'.format(line=line, **COLORS))

  # Unknown result
  if not (test.aborted or test.failed or test.passed):
    test.report.append('  {YELLOW}Unknown result{CLEAR}'.format(**COLORS))
    test.update_status('Unknown')

  # Add temps to report
  test.report.append('{BLUE}Temps{CLEAR}'.format(**COLORS))
  for line in generate_sensor_report(
      test.sensor_data, 'Idle', 'Max', 'Cooldown', cpu_only=True):
    test.report.append('  {}'.format(line))

  # Add abort message(s)
  if test.aborted:
    test.report.append(
      '  {YELLOW}Aborted{CLEAR}'.format(**COLORS))
  if test.thermal_abort:
    test.report.append(
      '  {RED}CPU reached temperature limit of {temp}°C{CLEAR}'.format(
        temp=THERMAL_LIMIT,
        **COLORS))

  # Done
  update_progress_pane(state)

  # Cleanup
  state.tmux_layout.pop('Current', None)
  tmux_kill_pane(
    state.panes.pop('Prime95', None),
    state.panes.pop('Temps', None),
    )
  test.monitor_proc.kill()


def run_network_test():
  """Run network test."""
  clear_screen()
  run_program(['hw-diags-network'], check=False, pipe=False)
  pause('Press Enter to return to main menu... ')


def run_nvme_smart_tests(state, test, update_mode=False):
  """Run NVMe or SMART test for test.dev.

  Update mode is used to refresh the attributes and recheck them.
  (i.e. no self-test and don't disable other tests)"""
  dev = test.dev

  # Bail early
  if test.disabled:
    return

  # Prep
  print_log('Starting NVMe/SMART test for {}'.format(dev.path))
  test.started = True
  test.update_status()
  update_progress_pane(state)

  # Update tmux layout
  state.set_top_pane_text(dev.description)

  # SMART short self-test
  if dev.smart_attributes and not (state.quick_mode or update_mode):
    run_smart_short_test(state, test)

  # Attribute check
  dev.check_attributes()

  # Check results
  if dev.nvme_attributes or state.quick_mode:
    if dev.disk_ok:
      test.passed = True
      test.update_status('CS')
    else:
      test.failed = True
      test.update_status('NS')
  elif dev.smart_attributes:
    if dev.disk_ok and dev.self_test_passed and 'OVERRIDE' not in test.status:
      test.passed = True
      test.update_status('CS')
    elif test.aborted:
      test.update_status('Aborted')
      raise GenericAbort('Aborted')
    elif dev.self_test_timed_out:
      test.failed = True
      test.update_status('TimedOut')
    elif dev.override_disabled or 'OVERRIDE' not in test.status:
      # override_disabled is set to True if one or more critical attributes
      # have exceeded the Error threshold. This overrules an override.
      test.failed = True
      test.update_status('NS')
  else:
    # This dev lacks both NVMe and SMART data. This test should've been
    # disabled during the safety_check().
    pass

  # Disable other disk tests if necessary
  if test.failed and not update_mode:
    for t in ['badblocks', 'I/O Benchmark']:
      dev.disable_test(t, 'Denied')

  # Done
  update_progress_pane(state)


def run_smart_short_test(state, test):
  """Run SMART short self-test for test.dev."""
  dev = test.dev
  dev.self_test_started = False
  dev.self_test_finished = False
  dev.self_test_passed = False
  dev.self_test_timed_out = False
  test.timeout = dev.smart_self_test['polling_minutes'].get('short', 5)
  test.timeout = int(test.timeout) + 5

  # Create monitor pane
  test.smart_out = '{}/smart_{}.out'.format(global_vars['LogDir'], dev.name)
  with open(test.smart_out, 'w') as f:
    f.write('SMART self-test status:\n  Starting...')
  state.panes['SMART'] = tmux_split_window(
    lines=3, vertical=True, watch=test.smart_out)

  # Show attributes
  clear_screen()
  show_report(dev.generate_attribute_report())
  print_standard(' ')

  # Start short test
  print_standard('Running self-test...')
  cmd = [
    'sudo',
    'smartctl',
    '--tolerance=normal',
    '--test=short',
    dev.path,
    ]
  run_program(cmd, check=False)

  # Monitor progress
  try:
    for i in range(int(test.timeout*60/5)):
      sleep(5)

      # Update SMART data
      dev.get_smart_details()

      if dev.self_test_started:
        # Update progress file
        with open(test.smart_out, 'w') as f:
          f.write('SMART self-test status:\n  {}'.format(
            dev.smart_self_test['status'].get(
              'string', 'UNKNOWN').capitalize()))

        # Check if test has finished
        if 'remaining_percent' not in dev.smart_self_test['status']:
          dev.self_test_finished = True
          break

      else:
        # Check if test has started
        if 'remaining_percent' in dev.smart_self_test['status']:
          dev.self_test_started = True
  except KeyboardInterrupt:
    # Will be handled in run_nvme_smart_tests()
    test.aborted = True

  # Save report
  test.report.append('{BLUE}SMART Short self-test{CLEAR}'.format(**COLORS))
  test.report.append('  {}'.format(
    dev.smart_self_test['status'].get('string', 'UNKNOWN').capitalize()))
  if dev.self_test_finished:
    dev.self_test_passed = dev.smart_self_test['status'].get('passed', False)
  elif test.aborted:
    test.report.append('  {YELLOW}Aborted{CLEAR}'.format(**COLORS))
  else:
    dev.self_test_timed_out = True
    test.report.append('  {YELLOW}Timed out{CLEAR}'.format(**COLORS))

  # Cleanup
  tmux_kill_pane(state.panes.pop('SMART', None))


def secret_screensaver(screensaver=None):
  """Show screensaver."""
  if screensaver == 'matrix':
    cmd = 'cmatrix -abs'.split()
  elif screensaver == 'pipes':
    cmd = 'pipes -t 0 -t 1 -t 2 -t 3 -p 5 -R -r 4000'.split()
  else:
    raise Exception('Invalid screensaver')
  run_program(cmd, check=False, pipe=False)


def show_report(report, log_report=False):
  """Show report on screen and optionally save to log w/out color."""
  for line in report:
    print(line)
    if log_report:
      print_log(strip_colors(line))


def show_results(state):
  """Show results for all tests."""
  clear_screen()
  state.set_top_pane_text('Results')

  # CPU tests
  _enabled = False
  for k in TESTS_CPU:
    if state.tests[k]['Enabled']:
      _enabled = True
  if _enabled:
    print_success('CPU:'.format(k))
    show_report(state.cpu.generate_cpu_report(), log_report=True)
    print_standard(' ')

  # Disk tests
  _enabled = False
  for k in TESTS_DISK:
    if state.tests[k]['Enabled']:
      _enabled = True
  if _enabled:
    print_success('Disk{}:'.format(
      '' if len(state.disks) == 1 else 's'))
    for disk in state.disks:
      show_report(disk.generate_disk_report(), log_report=True)
      print_standard(' ')
    if not state.disks:
      print_warning('No devices')
      print_standard(' ')

  # Update progress
  update_progress_pane(state)


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
