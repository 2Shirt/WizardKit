# Wizard Kit: Debug - HW Diagnostics

import base64
import requests

from functions.common import *

def debug_report_cpu(cpu_obj):
  """Generate report for CpuObj, returns list."""
  report = []

  # CPU Info
  report.append('CPU: {}'.format(cpu_obj.name))
  report.append('lscpu:')
  for k, v in sorted(cpu_obj.lscpu.items()):
    report.append('  {}: {}'.format(k, v))

  # Tests
  report.append('Tests:')
  for k, v in cpu_obj.tests.items():
    report.extend(debug_report_test(v, k))

  # Done
  return report


def debug_report_disk(disk_obj):
  """Generate report for DiskObj, returns list."""
  report = []
  expand = [
    'lsblk',
    'nvme_attributes',
    'nvme_smart_notes',
    'smart_attributes',
    'smart_self_test',
    'smartctl',
    ]
  skip = [
    'add_nvme_smart_note',
    'calc_io_dd_values',
    'check_attributes',
    'check_smart_self_test',
    'description',
    'disable_test',
    'generate_attribute_report',
    'generate_disk_report',
    'get_details',
    'get_size',
    'get_smart_details',
    'name',
    'safety_check',
    'tests',
    ]

  # Disk Info
  report.append('Disk: {} {}'.format(
    disk_obj.name, disk_obj.description))
  for a in dir(disk_obj):
    if a.startswith('_') or a in skip:
      continue
    if a in expand:
      report.append('{}:'.format(a))
      attr = getattr(disk_obj, a)
      try:
        for k, v in sorted(attr.items()):
          report.append('  {}: {}'.format(k, v))
      except Exception:
        # Ignore
        pass
    else:
      report.append('{}: {}'.format(a, getattr(disk_obj, a)))

  # Tests
  report.append('Tests:')
  for k, v in disk_obj.tests.items():
    report.extend(debug_report_test(v, k))

  # Done
  return report


def debug_report_state(state):
  """Generate report for State, returns list."""
  report = []

  # Devs
  report.append('CPU: {}'.format(state.cpu))
  report.append('Disks: {}'.format(state.disks))

  # Settings
  report.append('Progress Out: {}'.format(state.progress_out))
  report.append('Quick Mode: {}'.format(state.quick_mode))

  # Tests
  report.append('Tests:')
  for k, v in state.tests.items():
    report.append('  {}:'.format(k))
    for k2, v2 in sorted(v.items()):
      report.append('    {}: {}'.format(k2, v2))

  # tmux
  if hasattr(state, 'tmux_layout'):
    report.append('tmux Layout:')
    for k, v in state.tmux_layout.items():
      report.append('  {}: {}'.format(k, str(v)))
  if hasattr(state, 'panes'):
    report.append('tmux Panes:')
    for k, v in state.panes.items():
      report.append('  {}: {}'.format(k, str(v)))

  # Done
  return report


def debug_report_test(test_obj, test_name):
  """Generate report for TestObj, returns list."""
  report = ['  {}:'.format(test_name)]
  skip = ['update_status']

  # Attributes
  for a in [a for a in dir(test_obj) if not a.startswith('_')]:
    if a in skip:
      continue
    report.append('    {}: {}'.format(a, getattr(test_obj, a)))

  # Done
  return report


def save_debug_reports(state, global_vars):
  """Save debug reports if possible."""
  debug_dest = '{}/debug'.format(global_vars['LogDir'])
  os.makedirs(debug_dest, exist_ok=True)

  # State
  with open('{}/state.report'.format(debug_dest), 'a') as f:
    for line in debug_report_state(state):
      f.write('{}\n'.format(line))

  # CPU
  with open('{}/cpu.report'.format(debug_dest), 'a') as f:
    for line in debug_report_cpu(state.cpu):
      f.write('{}\n'.format(line))

  # Disk(s)
  for disk in state.disks:
    with open('{}/disk_{}.report'.format(debug_dest, disk.name), 'a') as f:
      for line in debug_report_disk(disk):
        f.write('{}\n'.format(line))


def upload_logdir(global_vars, reason='Crash'):
  """Upload compressed LogDir to CRASH_SERVER."""
  source = global_vars['LogDir']
  source = source[source.rfind('/')+1:]
  dest = 'HW-Diags_{reason}_{Date-Time}.txz'.format(
    reason=reason,
    **global_vars,
    )
  data = None

  # Compress LogDir
  os.chdir('{}/..'.format(global_vars['LogDir']))
  cmd = ['tar', 'caf', dest, source]
  run_program(cmd)

  # Read file
  with open(dest, 'rb') as f:
    data = f.read()

  # Upload data
  url = '{}/{}'.format(CRASH_SERVER['Url'], dest)
  r = requests.put(
    url,
    data=data,
    headers={'X-Requested-With': 'XMLHttpRequest'},
    auth=(CRASH_SERVER['User'], CRASH_SERVER['Pass']))
  # Raise exception if upload NS
  if not r.ok:
    raise GenericError


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
