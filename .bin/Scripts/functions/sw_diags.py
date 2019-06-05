# Wizard Kit: Functions - SW Diagnostics

import ctypes

from functions.common import *
from settings.sw_diags import *


def check_4k_alignment(show_alert=False):
  """Check that all partitions are 4K aligned."""
  aligned = True
  cmd = ['WMIC', 'partition', 'get', 'StartingOffset']
  offsets = []

  # Get offsets
  result = run_program(cmd, encoding='utf-8', errors='ignore', check=False)
  offsets = result.stdout.splitlines()

  # Check offsets
  for off in offsets:
    off = off.strip()
    if not off.isnumeric():
      # Skip
      continue

    try:
      aligned = aligned and int(off) % 4096 == 0
    except ValueError:
      # Ignore, this check is low priority
      pass

  # Show alert
  if show_alert:
    show_alert_box('One or more partitions are not 4K aligned')
    raise Not4KAlignedError


def check_connection():
  """Check if the system is online and optionally abort the script."""
  while True:
    result = try_and_print(message='Ping test...',  function=ping, cs='OK')
    if result['CS']:
      break
    if not ask('ERROR: System appears offline, try again?'):
      if ask('Continue anyway?'):
        break
      else:
        abort()


def check_secure_boot_status(show_alert=False):
  """Checks UEFI Secure Boot status via PowerShell."""
  boot_mode = get_boot_mode()
  cmd = ['PowerShell', '-Command', 'Confirm-SecureBootUEFI']
  result = run_program(cmd, check=False)

  # Check results
  if result.returncode == 0:
    out = result.stdout.decode()
    if 'True' in out:
      # It's on, do nothing
      return
    elif 'False' in out:
      if show_alert:
        show_alert_box('Secure Boot DISABLED')
      raise SecureBootDisabledError
    else:
      if show_alert:
        show_alert_box('Secure Boot status UNKNOWN')
      raise SecureBootUnknownError
  else:
    if boot_mode != 'UEFI':
      if (show_alert and
        global_vars['OS']['Version'] in ('8', '8.1', '10')):
        # OS supports Secure Boot
        show_alert_box('Secure Boot DISABLED\n\nOS installed LEGACY')
      raise OSInstalledLegacyError
    else:
      # Check error message
      err = result.stderr.decode()
      if 'Cmdlet not supported' in err:
        if show_alert:
          show_alert_box('Secure Boot UNAVAILABLE?')
        raise SecureBootNotAvailError
      else:
        if show_alert:
          show_alert_box('Secure Boot ERROR')
        raise GenericError


def get_boot_mode():
  """Check if Windows is booted in UEFI or Legacy mode, returns str."""
  kernel = ctypes.windll.kernel32
  firmware_type = ctypes.c_uint()

  # Get value from kernel32 API
  try:
    kernel.GetFirmwareType(ctypes.byref(firmware_type))
  except:
    # Just set to zero
    firmware_type = ctypes.c_uint(0)

  # Set return value
  type_str = 'Unknown'
  if firmware_type.value == 1:
    type_str = 'Legacy'
  elif firmware_type.value == 2:
    type_str = 'UEFI'

  return type_str


def os_is_unsupported(show_alert=False):
  """Checks if the current OS is unsupported, returns bool."""
  msg = ''
  unsupported = False

  # Check OS version/notes
  os_info = global_vars['OS'].copy()
  if os_info['Notes'] == 'unsupported':
    msg = 'The installed version of Windows is no longer supported'
    unsupported = True
  elif os_info['Notes'] == 'preview build':
    msg = 'Preview builds are not officially supported'
    unsupported = True
  elif os_info['Version'] == '10' and os_info['Notes'] == 'outdated':
    msg = 'The installed version of Windows is outdated'
    unsupported = True
  if 'Preview' not in msg:
    msg += '\n\nPlease consider upgrading before continuing setup.'

  # Show alert
  if unsupported and show_alert:
    show_alert_box(msg)

  # Done
  return unsupported


def run_autoruns():
  """Run AutoRuns in the background with VirusTotal checks enabled."""
  extract_item('Autoruns', filter='autoruns*', silent=True)
  # Update AutoRuns settings before running
  for path, settings in AUTORUNS_SETTINGS.items():
    winreg.CreateKey(HKCU, path)
    with winreg.OpenKey(HKCU, path, access=winreg.KEY_WRITE) as key:
      for name, value in settings.items():
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
  popen_program(global_vars['Tools']['AutoRuns'], minimized=True)


def run_hwinfo_sensors():
  """Run HWiNFO sensors."""
  path = r'{BinDir}\HWiNFO'.format(**global_vars)
  for bit in [32, 64]:
    # Configure
    source = r'{}\general.ini'.format(path)
    dest =   r'{}\HWiNFO{}.ini'.format(path, bit)
    shutil.copy(source, dest)
    with open(dest, 'a') as f:
      f.write('SensorsOnly=1\n')
      f.write('SummaryOnly=0\n')
  popen_program(global_vars['Tools']['HWiNFO'])


def run_nircmd(*cmd):
  """Run custom NirCmd."""
  extract_item('NirCmd', silent=True)
  cmd = [global_vars['Tools']['NirCmd'], *cmd]
  run_program(cmd, check=False)


def run_xmplay():
  """Run XMPlay to test audio."""
  extract_item('XMPlay', silent=True)
  cmd = [global_vars['Tools']['XMPlay'],
    r'{BinDir}\XMPlay\music.7z'.format(**global_vars)]

  # Unmute audio first
  extract_item('NirCmd', silent=True)
  run_nircmd('mutesysvolume', '0')

  # Open XMPlay
  popen_program(cmd)


def run_hitmanpro():
  """Run HitmanPro in the background."""
  extract_item('HitmanPro', silent=True)
  cmd = [
    global_vars['Tools']['HitmanPro'],
    '/quiet', '/noinstall', '/noupload',
    r'/log={LogDir}\Tools\HitmanPro.txt'.format(**global_vars)]
  popen_program(cmd)


def run_process_killer():
  """Kill most running processes skipping those in the whitelist.txt."""
  # borrowed from TronScript (reddit.com/r/TronScript)
  # credit to /u/cuddlychops06
  prev_dir = os.getcwd()
  extract_item('ProcessKiller', silent=True)
  os.chdir(r'{BinDir}\ProcessKiller'.format(**global_vars))
  run_program(['ProcessKiller.exe', '/silent'], check=False)
  os.chdir(prev_dir)


def run_rkill():
  """Run RKill and cleanup afterwards."""
  extract_item('RKill', silent=True)
  cmd = [
    global_vars['Tools']['RKill'],
    '-s', '-l', r'{LogDir}\Tools\RKill.log'.format(**global_vars),
    '-new_console:n', '-new_console:s33V']
  run_program(cmd, check=False)
  wait_for_process('RKill')

  # RKill cleanup
  desktop_path = r'{USERPROFILE}\Desktop'.format(**global_vars['Env'])
  if os.path.exists(desktop_path):
    for item in os.scandir(desktop_path):
      if re.search(r'^RKill', item.name, re.IGNORECASE):
        dest = r'{LogDir}\Tools\{name}'.format(
          name=dest, **global_vars)
        dest = non_clobber_rename(dest)
        shutil.move(item.path, dest)


def show_alert_box(message, title='Wizard Kit Warning'):
  """Show Windows alert box with message."""
  message_box = ctypes.windll.user32.MessageBoxW
  message_box(None, message, title, 0x00001030)


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
