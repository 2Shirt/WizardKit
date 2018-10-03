# Wizard Kit: Functions - Diagnostics

import ctypes

from functions.common import *

# STATIC VARIABLES
AUTORUNS_SETTINGS = {
    r'Software\Sysinternals\AutoRuns': {
        'checkvirustotal': 1,
        'EulaAccepted': 1,
        'shownomicrosoft': 1,
        'shownowindows': 1,
        'showonlyvirustotal': 1,
        'submitvirustotal': 0,
        'verifysignatures': 1,
        },
    r'Software\Sysinternals\AutoRuns\SigCheck': {
        'EulaAccepted': 1,
        },
    r'Software\Sysinternals\AutoRuns\Streams': {
        'EulaAccepted': 1,
        },
    r'Software\Sysinternals\AutoRuns\VirusTotal': {
        'VirusTotalTermsAccepted': 1,
        },
    }

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

def check_secure_boot_status():
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
            raise SecureBootDisabledError
        else:
            raise SecureBootUnknownError
    else:
        if boot_mode != 'UEFI':
            raise OSInstalledLegacyError
        else:
          # Check error message
          err = result.stderr.decode()
          if 'Cmdlet not supported' in err:
              raise SecureBootNotAvailError
          else:
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
    run_nircmd(['mutesysvolume', '0'])

    # Open XMPlay
    popen_program(cmd)

def run_hitmanpro():
    """Run HitmanPro in the background."""
    extract_item('HitmanPro', silent=True)
    cmd = [
        global_vars['Tools']['HitmanPro'],
        '/quiet', '/noinstall', '/noupload',
        r'/log={LogDir}\hitman.xml'.format(**global_vars)]
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
        '-l', r'{LogDir}\RKill.log'.format(**global_vars),
        '-new_console:n', '-new_console:s33V']
    run_program(cmd, check=False)
    wait_for_process('RKill')
    kill_process('notepad.exe')

    # RKill cleanup
    desktop_path = r'{USERPROFILE}\Desktop'.format(**global_vars['Env'])
    if os.path.exists(desktop_path):
        for item in os.scandir(desktop_path):
            if re.search(r'^RKill', item.name, re.IGNORECASE):
                dest = re.sub(r'^(.*)\.', '\1_{Date-Time}.'.format(
                    **global_vars), item.name)
                dest = r'{ClientDir}\Info\{name}'.format(
                    name=dest, **global_vars)
                dest = non_clobber_rename(dest)
                shutil.move(item.path, dest)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
