# Wizard Kit: Functions - Common

import os
import psutil
import re
import shutil
import subprocess
import sys
import time
import traceback
import winreg

from subprocess import CalledProcessError

from settings.main import *
from settings.tools import *

# Global variables
global_vars = {}

# STATIC VARIABLES
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'
}
HKU = winreg.HKEY_USERS
HKCU = winreg.HKEY_CURRENT_USER
HKLM = winreg.HKEY_LOCAL_MACHINE

# Error Classes
class BinNotFoundError(Exception):
    pass

class GenericError(Exception):
    pass

class GenericRepair(Exception):
    pass

class MultipleInstallationsError(Exception):
    pass

class NotInstalledError(Exception):
    pass

class NoProfilesError(Exception):
    pass

class PathNotFoundException(Exception):
    pass

class UnsupportedOSError(Exception):
    pass

# General functions
def abort():
    """Abort script."""
    print_warning('Aborted.')
    sleep(5)
    exit_script()

def ask(prompt='Kotaero!'):
    """Prompt the user with a Y/N question, log answer, and return a bool."""
    answer = None
    prompt = '{} [Y/N]: '.format(prompt)
    while answer is None:
        tmp = input(prompt)
        if re.search(r'^y(es|)$', tmp, re.IGNORECASE):
            answer = True
        elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
            answer = False
    message = '{prompt}{answer_text}'.format(
        prompt = prompt,
        answer_text = 'Yes' if answer else 'No')
    print_log(message=message)
    return answer

def convert_to_bytes(size):
    """Convert human-readable size str to bytes and return an int."""
    size = str(size)
    tmp = re.search(r'(\d+)\s+([KMGT]B)', size.upper())
    if tmp:
        size = int(tmp.group(1))
        units = tmp.group(2)
        if units == 'TB':
            size *= 1099511627776
        elif units == 'GB':
            size *= 1073741824
        elif units == 'MB':
            size *= 1048576
        elif units == 'KB':
            size *= 1024
    else:
        return -1

    return size

def exit_script(return_value=0):
    """Exits the script after some cleanup and opens the log (if set)."""
    # Remove dirs (if empty)
    for dir in ['BackupDir', 'LogDir', 'TmpDir']:
        try:
            dir = global_vars[dir]
            os.rmdir(dir)
        except Exception:
            pass

    # Open Log (if it exists)
    log = global_vars.get('LogFile', '')
    if log and os.path.exists(log):
        try:
            extract_item('NotepadPlusPlus', silent=True)
            popen_program(
                [global_vars['Tools']['NotepadPlusPlus'],
                global_vars['LogFile']])
        except Exception:
            print_error('ERROR: Failed to extract Notepad++ and open log.')
            pause('Press Enter to exit...')

    # Kill Caffeine if still running
    kill_process('caffeine.exe')

    # Exit
    sys.exit(return_value)

def extract_item(item, filter='', silent=False):
    """Extract item from .cbin into .bin."""
    cmd = [
        global_vars['Tools']['SevenZip'], 'x', '-aos', '-bso0', '-bse0',
        '-p{ArchivePassword}'.format(**global_vars),
        r'-o{BinDir}\{item}'.format(item=item, **global_vars),
        r'{CBinDir}\{item}.7z'.format(item=item, **global_vars),
        filter]
    if not silent:
        print_standard('Extracting "{item}"...'.format(item=item))
    try:
        run_program(cmd)
    except subprocess.CalledProcessError:
        if not silent:
            print_warning('WARNING: Errors encountered while exctracting data')

def get_ticket_number():
    """Get TicketNumber from user, save in LogDir, and return as str."""
    ticket_number = None
    while ticket_number is None:
        _input = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([-_]?\w+|))$', _input):
            ticket_number = _input
            with open(r'{LogDir}\TicketNumber'.format(**global_vars), 'w') as f:
                f.write(ticket_number)
    return ticket_number

def human_readable_size(size, decimals=0):
    """Convert size in bytes to a human-readable format and return a str."""
    # Prep string formatting
    width = 3+decimals
    if decimals > 0:
        width += 1

    # Convert size to int
    try:
        size = int(size)
    except ValueError:
        size = convert_to_bytes(size)

    # Verify we have a valid size
    if size <= 0:
        return '{size:>{width}} b'.format(size='???', width=width)

    # Convert to sensible units
    if size >= 1099511627776:
        size /= 1099511627776
        units = 'Tb'
    elif size >= 1073741824:
        size /= 1073741824
        units = 'Gb'
    elif size >= 1048576:
        size /= 1048576
        units = 'Mb'
    elif size >= 1024:
        size /= 1024
        units = 'Kb'
    else:
        units = ' b'
    
    # Return
    return '{size:>{width}.{decimals}f} {units}'.format(
        size=size, width=width, decimals=decimals, units=units)

def kill_process(name):
    """Kill any running caffeine.exe processes."""
    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()

def major_exception():
    """Display traceback and exit"""
    print_error('Major exception')
    print_warning(
        "  Please let {tech} know and they'll look into it"
        " (include the details below).".format(tech=SUPPORT_TECH))
    print(traceback.format_exc())
    print_log(traceback.format_exc())
    sleep(30)
    pause('Press Enter to exit...')
    # sys.exit(1)
    exit_script(1)

def menu_select(title='~ Untitled Menu ~',
    prompt='Please make a selection', secret_exit=False,
    main_entries=[], action_entries=[], disabled_label='DISABLED'):
    """Display options in a menu and return selected option as a str."""
    # Bail early
    if not main_entries and not action_entries:
        raise Exception("MenuError: No items given")

    # Build menu
    menu_splash =   '{}\n\n'.format(title)
    width =         len(str(len(main_entries)))
    valid_answers = []
    if (secret_exit):
        valid_answers.append('Q')

    # Add main entries
    for i in range(len(main_entries)):
        entry = main_entries[i]
        # Add Spacer
        if ('CRLF' in entry):
            menu_splash += '\n'
        entry_str = '{number:>{width}}: {name}'.format(
                number =    i+1,
                width =     width,
                name =      entry.get('Display Name', entry['Name']))
        if entry.get('Disabled', False):
            entry_str = '{YELLOW}{entry_str} ({disabled}){CLEAR}'.format(
                entry_str = entry_str,
                disabled =  disabled_label,
                **COLORS)
        else:
            valid_answers.append(str(i+1))
        menu_splash += '{}\n'.format(entry_str)
    menu_splash += '\n'

    # Add action entries
    for entry in action_entries:
        # Add Spacer
        if ('CRLF' in entry):
            menu_splash += '\n'
        valid_answers.append(entry['Letter'])
        menu_splash += '{letter:>{width}}: {name}\n'.format(
            letter =    entry['Letter'].upper(),
            width =     len(str(len(action_entries))),
            name =      entry['Name'])
    menu_splash += '\n'

    answer = ''

    while (answer.upper() not in valid_answers):
        os.system('cls')
        print(menu_splash)
        answer = input('{}: '.format(prompt))

    return answer.upper()

def non_clobber_rename(full_path):
    """Append suffix to path, if necessary, to avoid clobbering path"""
    new_path = full_path
    _i = 1;
    while os.path.exists(new_path):
        new_path = '{path}_{i}'.format(i=_i, path=full_path)
        _i += 1

    return new_path

def pause(prompt='Press Enter to continue... '):
    """Simple pause implementation."""
    input(prompt)

def ping(addr='google.com'):
    """Attempt to ping addr."""
    cmd = ['ping', '-n', '2', addr]
    run_program(cmd)

def popen_program(cmd, pipe=False, minimized=False, shell=False, **kwargs):
    """Run program and return a subprocess.Popen object."""
    startupinfo=None
    if minimized:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 6

    if pipe:
        popen_obj = subprocess.Popen(cmd, shell=shell, startupinfo=startupinfo,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        popen_obj = subprocess.Popen(cmd, shell=shell, startupinfo=startupinfo)

    return popen_obj

def print_error(*args, **kwargs):
    """Prints message to screen in RED."""
    print_standard(*args, color=COLORS['RED'], **kwargs)

def print_info(*args, **kwargs):
    """Prints message to screen in BLUE."""
    print_standard(*args, color=COLORS['BLUE'], **kwargs)

def print_warning(*args, **kwargs):
    """Prints message to screen in YELLOW."""
    print_standard(*args, color=COLORS['YELLOW'], **kwargs)

def print_standard(message='Generic info',
    color=None, end='\n', timestamp=True, **kwargs):
    """Prints message to screen and log (if set)."""
    display_message = message
    if color:
        display_message = color + message + COLORS['CLEAR']
    # **COLORS is used below to support non-"standard" color printing
    print(display_message.format(**COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_success(*args, **kwargs):
    """Prints message to screen in GREEN."""
    print_standard(*args, color=COLORS['GREEN'], **kwargs)

def print_log(message='', end='\n', timestamp=True):
    time_str = time.strftime("%Y-%m-%d %H%M%z: ") if timestamp else ''
    if 'LogFile' in global_vars and global_vars['LogFile'] is not None:
        with open(global_vars['LogFile'], 'a') as f:
            for line in message.splitlines():
                f.write('{timestamp}{line}{end}'.format(
                    timestamp = time_str,
                    line =      line,
                    end =       end))

def run_program(cmd, args=[], check=True, pipe=True, shell=False):
    """Run program and return a subprocess.CompletedProcess object."""
    if args:
        # Deprecated so let's raise an exception to find & fix all occurances
        print_error('ERROR: Using args is no longer supported.')
        raise Exception
    cmd = [c for c in cmd if c]
    if shell:
        cmd = ' '.join(cmd)

    if pipe:
        process_return = subprocess.run(cmd, check=check, shell=shell,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process_return = subprocess.run(cmd, check=check, shell=shell)

    return process_return

def show_info(message='~Some message~', info='~Some info~', indent=8, width=32):
    """Display info with formatting."""
    print_standard('{indent}{message:<{width}}{info}'.format(
        indent=' '*indent, width=width, message=message, info=info))

def sleep(seconds=2):
    """Wait for a while."""
    time.sleep(seconds)

def stay_awake():
    """Prevent the system from sleeping or hibernating."""
    # Bail if caffeine is already running
    for proc in psutil.process_iter():
        if proc.name() == 'caffeine.exe':
            return
    # Extract and run
    extract_item('Caffeine', silent=True)
    try:
        popen_program(global_vars['Tools']['Caffeine'])
    except Exception:
        print_error('ERROR: No caffeine available.')
        print_warning('Please set the power setting to High Performance.')

def get_exception(s):
    """Get exception by name, returns Exception object."""
    return getattr(sys.modules[__name__], s)

def try_and_print(message='Trying...',
    function=None, cs='CS', ns='NS', other_results={},
    catch_all=True, print_return=False, silent_function=True,
    indent=8, width=32, *args, **kwargs):
    """Run function, print if successful or not, and return dict.

    other_results is in the form of
        {
            'Warning': {'ExceptionClassName': 'Result Message'},
            'Error':   {'ExceptionClassName': 'Result Message'}
            }
        The the ExceptionClassNames will be excepted conditions
        and the result string will be printed in the correct color.
    catch_all=False will result in unspecified exceptions being re-raised."""
    err = None
    w_exceptions = other_results.get('Warning', {}).keys()
    w_exceptions = tuple(get_exception(e) for e in w_exceptions)
    e_exceptions = other_results.get('Error', {}).keys()
    e_exceptions = tuple(get_exception(e) for e in e_exceptions)
    w_results = other_results.get('Warning', {})
    e_results = other_results.get('Error', {})

    # Run function and catch errors
    print_standard('{indent}{message:<{width}}'.format(
        indent=' '*indent, message=message, width=width), end='', flush=True)
    try:
        out = function(*args, **kwargs)
        if print_return:
            print_standard(out[0], timestamp=False)
            for item in out[1:]:
                print_standard('{indent}{item}'.format(
                    indent=' '*(indent+width), item=item))
        elif silent_function:
            print_success(cs, timestamp=False)
    except w_exceptions as e:
        _result = w_results.get(e.__class__.__name__, 'Warning')
        print_warning(_result, timestamp=False)
        err = e
    except e_exceptions as e:
        _result = e_results.get(e.__class__.__name__, 'Error')
        print_error(_result, timestamp=False)
        err = e
    except Exception:
        print_error(ns, timestamp=False)
        err = traceback.format_exc()

    # Return or raise?
    if bool(err) and not catch_all:
        raise
    else:
        return {'CS': not bool(err), 'Error': err}

def upload_data(path, file):
    """Add CLIENT_INFO_SERVER to authorized connections and upload file."""
    if not ENABLED_UPLOAD_DATA:
        raise GenericError('Feature disabled.')
    
    extract_item('PuTTY', filter='wizkit.ppk psftp.exe', silent=True)

    # Authorize connection to the server
    winreg.CreateKey(HKCU, r'Software\SimonTatham\PuTTY\SshHostKeys')
    with winreg.OpenKey(HKCU, r'Software\SimonTatham\PuTTY\SshHostKeys',
        access=winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key,
            'rsa2@22:{IP}'.format(**CLIENT_INFO_SERVER), 0,
            winreg.REG_SZ, CLIENT_INFO_SERVER['RegEntry'])

    # Write batch file
    with open(r'{TmpDir}\psftp.batch'.format(**global_vars),
        'w', encoding='ascii') as f:
        f.write('lcd "{path}"\n'.format(path=path))
        f.write('cd "{Share}"\n'.format(**CLIENT_INFO_SERVER))
        f.write('mkdir {TicketNumber}\n'.format(**global_vars))
        f.write('cd {TicketNumber}\n'.format(**global_vars))
        f.write('put "{file}"\n'.format(file=file))

    # Upload Info
    cmd = [
        global_vars['Tools']['PuTTY-PSFTP'],
        '-noagent',
        '-i', r'{BinDir}\PuTTY\wizkit.ppk'.format(**global_vars),
        '{User}@{IP}'.format(**CLIENT_INFO_SERVER),
        '-b', r'{TmpDir}\psftp.batch'.format(**global_vars)]
    run_program(cmd)

def upload_info():
    """Upload compressed Info file to the NAS as set in settings.main.py."""
    if not ENABLED_UPLOAD_DATA:
        raise GenericError('Feature disabled.')
    
    path = '{ClientDir}'.format(**global_vars)
    file = 'Info_{Date-Time}.7z'.format(**global_vars)
    upload_data(path, file)

def compress_info():
    """Compress ClientDir info folders with 7-Zip for upload_info()."""
    path = '{ClientDir}'.format(**global_vars)
    file = 'Info_{Date-Time}.7z'.format(**global_vars)
    _cmd = [
        global_vars['Tools']['SevenZip'],
        'a', '-t7z', '-mx=9', '-bso0', '-bse0',
        r'{}\{}'.format(path, file),
        r'{ClientDir}\Info'.format(**global_vars)]
    run_program(_cmd)

def wait_for_process(name, poll_rate=3):
    """Wait for process by name."""
    running = True
    while running:
        sleep(poll_rate)
        running = False
        for proc in psutil.process_iter():
            if re.search(r'^{}'.format(name), proc.name(), re.IGNORECASE):
                running = True
    sleep(1)

# global_vars functions
def init_global_vars():
    """Sets global variables based on system info."""
    print_info('Initializing')
    os.system('title Wizard Kit')
    init_functions = [
        ['Checking .bin...',        find_bin],
        ['Checking environment...', set_common_vars],
        ['Checking OS...',          check_os],
        ['Checking tools...',       check_tools],
        ['Creating folders...',     make_tmp_dirs],
        ['Clearing collisions...',  clean_env_vars],
        ]
    try:
        for f in init_functions:
            try_and_print(
                message=f[0], function=f[1],
                cs='Done', ns='Error', catch_all=False)
    except:
        major_exception()

def check_os():
    """Set OS specific variables."""
    tmp = {}
    
    # Query registry
    _reg_path = winreg.OpenKey(
        HKLM, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    for key in ['CSDVersion', 'CurrentBuild', 'CurrentBuildNumber',
        'CurrentVersion', 'ProductName']:
        try:
            tmp[key] = winreg.QueryValueEx(_reg_path, key)[0]
            if key in ['CurrentBuild', 'CurrentBuildNumber']:
                tmp[key] = int(tmp[key])
        except ValueError:
            # Couldn't convert Build to int so this should be interesting...
            tmp[key] = 0
        except Exception:
            tmp[key] = 'Unknown'

    # Determine OS bit depth
    tmp['Arch'] = 32
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        tmp['Arch'] = 64

    # Determine OS Name
    tmp['Name'] = '{ProductName} {CSDVersion}'.format(**tmp)
    if tmp['CurrentBuild'] == 9600:
        tmp['Name'] += ' Update' # Win 8.1u
    if tmp['CurrentBuild'] == 10240:
        tmp['Name'] += ' Release 1507 "Threshold 1"'
    if tmp['CurrentBuild'] == 10586:
        tmp['Name'] += ' Release 1511 "Threshold 2"'
    if tmp['CurrentBuild'] == 14393:
        tmp['Name'] += ' Release 1607 "Redstone 1" / "Anniversary Update"'
    if tmp['CurrentBuild'] == 15063:
        tmp['Name'] += ' Release 1703 "Redstone 2" / "Creators Update"'
    if tmp['CurrentBuild'] == 16299:
        tmp['Name'] += ' Release 1709 "Redstone 3" / "Fall Creators Update"'
    tmp['Name'] = tmp['Name'].replace('Service Pack ', 'SP')
    tmp['Name'] = tmp['Name'].replace('Unknown Release', 'Release')
    tmp['Name'] = re.sub(r'\s+', ' ', tmp['Name'])

    # Determine OS version
    name = '{Name} x{Arch}'.format(**tmp)
    if tmp['CurrentVersion'] == '6.0':
        tmp['Version'] = 'Vista'
        name += ' (very outdated)'
    elif tmp['CurrentVersion'] == '6.1':
        tmp['Version'] = '7'
        if tmp['CSDVersion'] == 'Service Pack 1':
            name += ' (outdated)'
        else:
            name += ' (very outdated)'
    elif tmp['CurrentVersion'] in ['6.2', '6.3']:
        if int(tmp['CurrentBuildNumber']) <= 9600:
            tmp['Version'] = '8'
        elif int(tmp['CurrentBuildNumber']) >= 10240:
            tmp['Version'] = '10'
        if tmp['CurrentBuild'] in [9200, 10240, 10586]:
            name += ' (very outdated)'
        elif tmp['CurrentBuild'] in [9600, 14393, 15063]:
            name += ' (outdated)'
        elif tmp['CurrentBuild'] == 16299:
            pass # Current Win10
        else:
            name += ' (unrecognized)'
    tmp['DisplayName'] = name
    
    # == vista ==
    # 6.0.6000
    # 6.0.6001
    # 6.0.6002
    # ==== 7 ====
    # 6.1.7600
    # 6.1.7601
    # 6.1.7602
    # ==== 8 ====
    # 6.2.9200
    # === 8.1 ===
    # 6.3.9200
    # === 8.1u ==
    # 6.3.9600
    # === 10 v1507 "Threshold 1" ==
    # 6.3.10240
    # === 10 v1511 "Threshold 2" ==
    # 6.3.10586
    # === 10 v1607 "Redstone 1" "Anniversary Update" ==
    # 6.3.14393
    # === 10 v1703 "Redstone 2" "Creators Update" ==
    # 6.3.15063
    # === 10 v1709 "Redstone 3" "Fall Creators Update" ==
    # 6.3.16299
    global_vars['OS'] = tmp

def check_tools():
    """Set tool variables based on OS bit-depth and tool availability."""
    if global_vars['OS'].get('Arch', 32) == 64:
        global_vars['Tools'] = {k: v.get('64', v.get('32'))
            for (k, v) in TOOLS.items()}
    else:
        global_vars['Tools'] = {k: v.get('32') for (k, v) in TOOLS.items()}

    # Fix paths
    global_vars['Tools'] = {k: os.path.join(global_vars['BinDir'], v)
        for (k, v) in global_vars['Tools'].items()}

def clean_env_vars():
    """Remove conflicting global_vars and env variables.
    
    This fixes an issue where both global_vars and
    global_vars['Env'] are expanded at the same time."""
    for key in global_vars.keys():
        global_vars['Env'].pop(key, None)

def find_bin():
    """Find .bin folder in the cwd or it's parents."""
    wd = os.getcwd()
    base = None
    while base is None:
        if os.path.exists('.bin'):
            base = os.getcwd()
            break
        if re.fullmatch(r'\w:\\', os.getcwd()):
            break
        os.chdir('..')
    os.chdir(wd)
    if base is None:
        raise BinNotFoundError
    global_vars['BaseDir'] = base

def make_tmp_dirs():
    """Make temp directories."""
    os.makedirs(global_vars['BackupDir'], exist_ok=True)
    os.makedirs(global_vars['LogDir'], exist_ok=True)
    os.makedirs(global_vars['TmpDir'], exist_ok=True)

def set_common_vars():
    """Set common variables."""
    global_vars['Date'] =               time.strftime("%Y-%m-%d")
    global_vars['Date-Time'] =          time.strftime("%Y-%m-%d_%H%M_%z")
    global_vars['Env'] =                os.environ.copy()

    global_vars['ArchivePassword'] =    ARCHIVE_PASSWORD
    global_vars['BinDir'] =             r'{BaseDir}\.bin'.format(
        **global_vars)
    global_vars['CBinDir'] =            r'{BaseDir}\.cbin'.format(
        **global_vars)
    global_vars['ClientDir'] =          r'{SYSTEMDRIVE}\{prefix}'.format(
        prefix=KIT_NAME_SHORT, **global_vars['Env'])
    global_vars['BackupDir'] =          r'{ClientDir}\Backups\{Date}'.format(
        **global_vars)
    global_vars['LogDir'] =             r'{ClientDir}\Info\{Date}'.format(
        **global_vars)
    global_vars['ProgBackupDir'] =      r'{ClientDir}\Backups'.format(
        **global_vars)
    global_vars['QuarantineDir'] =      r'{ClientDir}\Quarantine'.format(
        **global_vars)
    global_vars['TmpDir'] =             r'{BinDir}\tmp'.format(
        **global_vars)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
