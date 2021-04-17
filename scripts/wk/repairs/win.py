"""WizardKit: Repairs - Windows"""
# vim: sts=2 sw=2 ts=2

import atexit
import logging
import os
import platform
import sys

from wk.cfg.main  import KIT_NAME_FULL
from wk.exe       import get_procs, run_program, popen_program, wait_for_procs
from wk.kit.tools import run_tool
from wk.log       import format_log_path, update_log_path
from wk.os.win    import reg_delete_value, reg_read_value, reg_set_value
from wk.std       import (
  GenericError,
  GenericWarning,
  TryAndPrint,
  abort,
  clear_screen,
  pause,
  print_info,
  set_title,
  sleep,
  )


# STATIC VARIABLES
LOG = logging.getLogger(__name__)
AUTO_REPAIR_DELAY_IN_SECONDS = 30
AUTO_REPAIR_KEY = fr'Software\{KIT_NAME_FULL}\AutoRepair'
CONEMU = 'ConEmuPID' in os.environ
OS_VERSION = float(platform.win32_ver()[0])
TRY_PRINT = TryAndPrint()


# AutoRepair Functions
def end_session():
  """End AutoRepair session."""
  print_info('Ending repair session')
  reg_delete_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')

  # Remove logon task
  cmd = [
    'schtasks', '/delete', '/f',
    '/tn', f'{KIT_NAME_FULL}-AutoRepair',
    ]
  run_program(cmd)

  # Disable Autologon
  run_tool('Sysinternals', 'Autologon')
  reg_set_value(
    'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
    'AutoAdminLogon', '0', 'SZ',
    )
  reg_delete_value(
    'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
    'DefaultUserName',
    )
  reg_delete_value(
    'HKLM', r'Software\Microsoft\Windows NT\CurrentVersion\Winlogon',
    'DefaultDomainName',
    )


def init():
  """Initialize AutoRepair."""
  session_started = False
  try:
    session_started = reg_read_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted')
  except FileNotFoundError:
    pass

  # Start or resume a repair session
  if not session_started:
    init_run()
    init_session()
  else:
    print_info('Resuming session, press CTRL+c to cancel')
    try:
      for _x in range(AUTO_REPAIR_DELAY_IN_SECONDS, 0, -1):
        print(f'  {_x} second{"" if _x==1 else "s"} remaining...  \r', end='')
        sleep(1)
    except KeyboardInterrupt:
      abort()
    print('')
    init_run()

  # Done
  return session_started


def init_run():
  """Initialize AutoRepair Run."""
  atexit.register(start_explorer)
  # TODO: Sync Clock
  kill_explorer()
  # TODO: RKill


def init_session():
  """Initialize AutoRepair session."""
  print_info('Starting repair session')
  reg_set_value('HKCU', AUTO_REPAIR_KEY, 'SessionStarted', 1, 'DWORD')

  # Create logon task for AutoRepair
  cmd = [
    'schtasks', '/create', '/f',
    '/sc', 'ONLOGON',
    '/tn', f'{KIT_NAME_FULL}-AutoRepair',
    '/rl', 'HIGHEST',
    '/tr', fr'C:\Windows\System32\cmd.exe "/C {sys.executable} {sys.argv[0]}"',
    ]
  run_program(cmd)

  # One-time tasks
  # TODO: Backup Registry
  # TODO: Enable and create restore point
  run_tool('Sysinternals', 'Autologon')
  # TODO: Disable Windows updates
  # TODO: Reset Windows updates
  reboot()


def run_auto_repair():
  """Run AutoRepair."""
  update_log_path(dest_name='Auto-Repair Tool', timestamp=True)
  title = f'{KIT_NAME_FULL}: Auto-Repair Tool'
  clear_screen()
  set_title(title)
  print_info(title)
  print('')

  # Show Menu on first run
  session_started = init()
  if not session_started:
    # TODO: Show Menu
    pass

  # Run repairs
  # TODO: Run repairs
  end_session()

  # Done
  print_info('Done')
  pause('Press Enter to exit...')


# OS Built-in Functions
def kill_explorer():
  """Kill all Explorer processes."""
  cmd = ['taskkill', '/im', 'explorer.exe', '/f']
  run_program(cmd, check=False)


def reboot():
  """Reboot the system."""
  atexit.unregister(start_explorer)
  cmd = ['shutdown', '-r', '-t', '0']
  run_program(cmd, check=False)
  raise SystemExit


def run_chkdsk_offline():
  """Set filesystem 'dirty bit' to force a CHKDSK during startup."""
  cmd = ['fsutil', 'dirty', 'set', os.environ.get('SYSTEMDRIVE', 'C:')]
  proc = run_program(cmd, check=False)

  # Check result
  if proc.returncode > 0:
    raise GenericError('Failed to set dirty bit.')


def run_chkdsk_online():
  """Run CHKDSK.

  NOTE: If run on Windows 8+ online repairs are attempted.
  """
  cmd = ['CHKDSK', os.environ.get('SYSTEMDRIVE', 'C:')]
  if OS_VERSION >= 8:
    cmd.extend(['/scan', '/perf'])
  if CONEMU:
    cmd.extend(['-new_console:n', '-new_console:s33V'])
  retried = False

  # Run scan
  run_program(cmd, check=False)
  try:
    proc = get_procs('chkdsk.exe')[0]
    return_code = proc.wait()
  except IndexError:
    # Failed to get CHKDSK process, set return_code to force a retry
    return_code = 255
  if return_code > 1:
    # Try again
    retried = True
    run_program(cmd, check=False)
    try:
      proc = get_procs('chkdsk.exe')[0]
      return_code = proc.wait()
    except IndexError:
      # Failed to get CHKDSK process
      return_code = -1

  # Check result
  if return_code == -1:
    raise GenericError('Failed to find CHKDSK process.')
  if (return_code == 0 and retried) or return_code == 1:
    raise GenericWarning('Repaired (or manually aborted)')
  if return_code > 1:
    raise GenericError('Issue(s) detected')


def run_dism(repair=True):
  """Run DISM to either scan or repair component store health."""
  conemu_args = ['-new_console:n', '-new_console:s33V'] if CONEMU else []

  # Bail early
  if OS_VERSION < 8:
    raise GenericWarning('Unsupported OS')

  # Run (repair) scan
  log_path = format_log_path(
    log_name=f'DISM_{"Restore" if repair else "Scan"}Health', tool=True,
    )
  cmd = [
    'DISM', '/Online', '/Cleanup-Image',
    '/RestoreHealth' if repair else '/ScanHealth',
    f'/LogPath:{log_path}',
    *conemu_args,
    ]
  run_program(cmd, check=False, pipe=False)
  wait_for_procs('dism.exe')

  # Run check health
  log_path = format_log_path(log_name='DISM_CheckHealth.log', tool=True)
  cmd = [
    'DISM', '/Online', '/Cleanup-Image',
    '/CheckHealth',
    f'/LogPath:{log_path}',
    ]
  proc = run_program(cmd, check=False)

  # Check for errors
  if 'no component store corruption detected' not in proc.stdout.lower():
    raise GenericError('Issue(s) detected')


def run_sfc_scan():
  """Run SFC and save results."""
  cmd = ['sfc', '/scannow']
  log_path = format_log_path(log_name='SFC', tool=True)
  err_path = log_path.with_suffix('.err')

  # Run SFC
  proc = run_program(cmd, check=False, encoding='utf-16le')

  # Save output
  os.makedirs(log_path.parent, exist_ok=True)
  with open(log_path, 'a') as _f:
    _f.write(proc.stdout)
  with open(err_path, 'a') as _f:
    _f.write(proc.stderr)

  # Check result
  if 'did not find any integrity violations' in proc.stdout:
    pass
  elif 'successfully repaired' in proc.stdout:
    raise GenericWarning('Repaired')
  elif 'found corrupt files' in proc.stdout:
    raise GenericError('Corruption detected')
  else:
    raise OSError


def start_explorer():
  """Start Explorer."""
  popen_program(['explorer.exe'])


if __name__ == '__main__':
  print("This file is not meant to be called directly.")
