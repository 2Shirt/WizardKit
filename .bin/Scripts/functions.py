# Wizard Kit: Init

import os
import partition_uids
import psutil
import re
import shutil
import subprocess
import sys
import time
import traceback
import winreg

from operator import itemgetter
from subprocess import CalledProcessError

# STATIC VARIABLES
ARCHIVE_PASSWORD='Abracadabra'
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'
}
BACKUP_SERVERS = [
    {   'IP':       '10.0.0.10',
        'Name':     'ServerOne',
        'Mounted':  False,
        'Share':    'Backups',
        'User':     'restore',
        'Pass':     'Abracadabra',
    },
    {   'IP':       '10.0.0.11',
        'Name':     'ServerTwo',
        'Mounted':  False,
        'Share':    'Backups',
        'User':     'restore',
        'Pass':     'Abracadabra',
    },
]
CLIENT_INFO_SERVER = {
    'IP':           '10.0.0.10',
    'RegEntry':     r'0x10001,0xcc674aebbd889f5fd553564adcf3cab550791eca12542033d52134db893c95aabb6b318a4621d8116f6838d873edfe9db4509e1dfc9177ee7484808a62cbc42b913387f694fd67e81950f85198acf721c5767b54db7b864d69cce65e12c78c87d0fb4fc54996609c9b9274b1de7bae2f95000c9ca8d7e3f9b3f2cdb21cd578adf9ba98d10400a8203bb1a879a4cd2fad99baeb12738b9b4b99fec821f881acb62598a43c059f74af287bc8dceeb4821317aa44e2e0ee66d346927a654c702854a71a2eaed6a53f6be9360c7049974a2597a548361da42ac982ae55f993700a8b1fc9f3b4458314fbd41f239de0a29716cdcefbbb2c8d02b4c2effa4163cfeac9',
    'Share':        '/srv/ClientInfo',
    'User':         'wkdiag',
}
OFFICE_SERVER = {
    'IP':           '10.0.0.10',
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Office',
    'User':         'restore',      # Using these credentials in case the backup shares are also mounted.
    'Pass':         'Abracadabra',   # This is because Windows only allows one set of credentials to be used per server at a time.
}
WINDOWS_SERVER = {
    'IP':           '10.0.0.10',
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Windows',
    'User':         'restore',      # Using these credentials in case the backup shares are also mounted.
    'Pass':         'Abracadabra',   # This is because Windows only allows one set of credentials to be used per server at a time.
}
SHELL_FOLDERS = {
    #GUIDs from: https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx
    'Desktop': ('{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}'),
    'Documents': ('Personal', '{FDD39AD0-238F-46AF-ADB4-6C85480369C7}'),
    'Downloads': ('{374DE290-123F-4565-9164-39C4925E467B}'),
    'Favorites': ('{1777F761-68AD-4D8A-87BD-30B759FA33DD}'),
    'Music': ('My Music', '{4BD8D571-6D19-48D3-BE97-422220080E43}'),
    'Pictures': ('My Pictures', '{33E28130-4E1E-4676-835A-98395C3BC3BB}'),
    'Videos': ('My Video', '{18989B1D-99B5-455B-841C-AB7C74E4DDFC}'),
}
EXTRA_FOLDERS = [
    'Dropbox',
    'Google Drive',
    'OneDrive',
    'SkyDrive',
]
TOOLS = {
    # NOTE: The brace variables will be expanded at runtime
    'AIDA64': {
        '32': '{BinDir}\\AIDA64\\aida64.exe'},
    'AutoRuns': {
        '32': '{BinDir}\\SysinternalsSuite\\autoruns.exe',
        '64': '{BinDir}\\SysinternalsSuite\\autoruns64.exe'},
    'BleachBit': {
        '32': '{BinDir}\\BleachBit\\bleachbit_console.exe'},
    'Caffeine': {
        '32': '{BinDir}\\caffeine\\caffeine.exe'},
    'curl': {
        '32': '{BinDir}\\curl\\curl.exe'},
    'Du': {
        '32': '{BinDir}\\SysinternalsSuite\\du.exe',
        '64': '{BinDir}\\SysinternalsSuite\\du64.exe'},
    'ERUNT': {
        '32': '{BinDir}\\erunt\\ERUNT.EXE'},
    'Everything': {
        '32': '{BinDir}\\Everything\\Everything.exe',
        '64': '{BinDir}\\Everything\\Everything64.exe'},
    'FastCopy': {
        '32': '{BinDir}\\FastCopy\\FastCopy.exe',
        '64': '{BinDir}\\FastCopy\\FastCopy64.exe'},
    'HitmanPro': {
        '32': '{BinDir}\\HitmanPro\\HitmanPro.exe',
        '64': '{BinDir}\\HitmanPro\\HitmanPro64.exe'},
    'HWiNFO': {
        '32': '{BinDir}\\HWiNFO\\HWiNFO.exe',
        '64': '{BinDir}\\HWiNFO\\HWiNFO64.exe'},
    'KVRT': {
        '32': '{BinDir}\\KVRT\\KVRT.exe'},
    'NotepadPlusPlus': {
        '32': '{BinDir}\\notepadplusplus\\notepadplusplus.exe'},
    'ProduKey': {
        '32': '{BinDir}\\ProduKey\\ProduKey.exe',
        '64': '{BinDir}\\ProduKey\\ProduKey64.exe'},
    'PuTTY-PSFTP': {
        '32': '{BinDir}\\PuTTY\\PSFTP.EXE'},
    'RKill': {
        '32': '{BinDir}\\RKill\\RKill.exe'},
    'SevenZip': {
        '32': '{BinDir}\\7-Zip\\7za.exe',
        '64': '{BinDir}\\7-Zip\\7za64.exe'},
    'TDSSKiller': {
        '32': '{BinDir}\\TDSSKiller\\TDSSKiller.exe'},
    'wimlib-imagex': {
        '32': '{BinDir}\\wimlib\\x32\\wimlib-imagex.exe',
        '64': '{BinDir}\\wimlib\\x64\\wimlib-imagex.exe'},
    'XMPlay': {
        '32': '{BinDir}\\XMPlay\\xmplay.exe'},
}
# Browsers
DEFAULT_HOMEPAGE = 'https://www.google.com/'
REGEX_CHROMIUM_ITEMS =  re.compile(r'^(Bookmarks|Cookies|Favicons|Google Profile|History|Login Data|Top Sites|TransportSecurity|Visited Links|Web Data).*', re.IGNORECASE)
REGEX_FIREFOX =         re.compile(r'^(bookmarkbackups|(cookies|formhistory|places).sqlite|key3.db|logins.json|persdict.dat)$', re.IGNORECASE)
REGEX_OFFICE =          re.compile(r'(Microsoft (Office\s+(365|Enterprise|Home|Pro(\s|fessional)|Single|Small|Standard|Starter|Ultimate|system)|Works[-\s\d]+\d)|(Libre|Open|Star)\s*Office|WordPerfect|Gnumeric|Abiword)', re.IGNORECASE)
# Registry
REGEX_REGISTRY_DIRS =   re.compile(r'^(config$|RegBack$|System32$|Transfer|Win)', re.IGNORECASE)
REGEX_SOFTWARE_HIVE =   re.compile(r'^Software$', re.IGNORECASE)
# Data 1
REGEX_EXCL_ITEMS =      re.compile(r'^(\.(AppleDB|AppleDesktop|AppleDouble|com\.apple\.timemachine\.supported|dbfseventsd|DocumentRevisions-V100.*|DS_Store|fseventsd|PKInstallSandboxManager|Spotlight.*|SymAV.*|symSchedScanLockxz|TemporaryItems|Trash.*|vol|VolumeIcon\.icns)|desktop\.(ini|.*DB|.*DF)|(hiberfil|pagefile)\.sys|lost\+found|Network\.*Trash\.*Folder|Recycle[dr]|System\.*Volume\.*Information|Temporary\.*Items|Thumbs\.db)$', flags=re.IGNORECASE)
REGEX_EXCL_ROOT_ITEMS = re.compile(r'^\\?(boot(mgr|nxt)$|Config.msi|(eula|globdata|install|vc_?red)|.*.sys$|System Volume Information|RECYCLER?|\$Recycle\.bin|\$?Win(dows(.old.*|\.~BT|)$|RE_)|\$GetCurrent|PerfLogs|Program Files|.*\.(esd|swm|wim|dd|map|dmg|image)$|SYSTEM.SAV|Windows10Upgrade)', flags=re.IGNORECASE)
REGEX_INCL_ROOT_ITEMS = re.compile(r'^\\?(AdwCleaner|(My\s*|)(Doc(uments?( and Settings|)|s?)|Downloads|WK(-?Info|-?Transfer|)|Media|Music|Pic(ture|)s?|Vid(eo|)s?)|(ProgramData|Recovery|Temp.*|Users)$|.*\.(log|txt|rtf|qb\w*|avi|m4a|m4v|mp4|mkv|jpg|png|tiff?)$)', flags=re.IGNORECASE)
REGEX_WIM_FILE =        re.compile(r'\.wim$', flags=re.IGNORECASE)
REGEX_WINDOWS_OLD =     re.compile(r'^\\Win(dows|)\.old', flags=re.IGNORECASE)
FAST_COPY_ARGS =        [
    '/cmd=noexist_only',
    '/utf8',
    '/skip_empty_dir',
    '/linkdest',
    '/no_ui',
    '/auto_close',
    r'/exclude=\*.esd;\*.swm;\*.wim;\*.dd;\*.dd.tgz;\*.dd.txz;\*.map;\*.dmg;\*.image;$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']
VCR_REDISTS = [
    {'Name': 'Visual C++ 2005 SP1 x32...',      'Cmd': ['msiexec', '/i', '2005sp1\\x86\\vcredist.msi', '/qb!', '/norestart']},
    {'Name': 'Visual C++ 2005 SP1 x64...',      'Cmd': ['msiexec', '/i', '2005sp1\\x64\\vcredist.msi', '/qb!', '/norestart']},
    {'Name': 'Visual C++ 2008 SP1 x32...',      'Cmd': ['2008sp1\\vcredist_x86.exe', '/qb! /norestart']},
    {'Name': 'Visual C++ 2008 SP1 x64...',      'Cmd': ['2008sp1\\vcredist_x64.exe', '/qb! /norestart']},
    {'Name': 'Visual C++ 2010 x32...',          'Cmd': ['2010\\vcredist_x86.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2010 x64...',          'Cmd': ['2010\\vcredist_x64.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2012 Update 4 x32...', 'Cmd': ['2012u4\\vcredist_x86.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2012 Update 4 x64...', 'Cmd': ['2012u4\\vcredist_x64.exe', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2013 x32...',          'Cmd': ['2013\\vcredist_x86.exe', '/install', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2013 x64...',          'Cmd': ['2013\\vcredist_x64.exe', '/install', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2015 Update 3 x32...', 'Cmd': ['2015u3\\vc_redist.x86.exe', '/install', '/passive', '/norestart']},
    {'Name': 'Visual C++ 2015 Update 3 x64...', 'Cmd': ['2015u3\\vc_redist.x64.exe', '/install', '/passive', '/norestart']}]

global_vars = {}

# Error Classes
class BIOSKeyNotFoundError(Exception):
    pass

class BinNotFoundError(Exception):
    pass

class GenericError(Exception):
    pass

class GenericRepair(Exception):
    pass

class NotInstalledError(Exception):
    pass

class NoProfilesError(Exception):
    pass

class UnsupportedOSError(Exception):
    pass

# General functions
def ask(prompt='Kotaero!'):
    """Prompt the user with a Y/N question, log answer, and return a bool."""
    answer = None
    prompt = prompt + ' [Y/N]: '
    while answer is None:
        tmp = input(prompt)
        if re.search(r'^y(es|)$', tmp, re.IGNORECASE):
            answer = True
        elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
            answer = False
    _message = '{prompt}{answer_text}'.format(
        prompt =        prompt,
        answer_text =   'Yes' if answer else 'No')
    print_log(message=_message)
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

def exit_script():
    # Remove dirs (if empty)
    for dir in ['BackupDir', 'LogDir', 'TmpDir']:
        try:
            dir = global_vars[dir]
            os.rmdir(dir)
        except:
            pass

    # Open Log (if it exists)
    _log = global_vars.get('LogFile', '')
    if os.path.exists(_log):
        try:
            extract_item('NotepadPlusPlus', silent=True)
            popen_program([global_vars['Tools']['NotepadPlusPlus'], global_vars['LogFile']])
        except:
            print_error('ERROR: Failed to extract Notepad++ and open log.')

    # Kill Caffeine if still running
    kill_process('caffeine.exe')

    # Exit
    sys.exit(0)

def extract_item(item=None, filter='', silent=False):
    """Extract item from .cbin into .bin."""
    if item is None:
        raise Exception
    _cmd = [
        global_vars['Tools']['SevenZip'], 'x', '-aos', '-bso0', '-bse0',
        '-p{ArchivePassword}'.format(**global_vars),
        '-o"{BinDir}\\{item}"'.format(item=item, **global_vars),
        '"{CBinDir}\\{item}.7z"'.format(item=item, **global_vars),
        filter]
    if not silent:
        print_standard('Extracting "{item}"...'.format(item=item))
    try:
        run_program(_cmd, shell=True)
    except subprocess.CalledProcessError:
        if not silent:
            print_warning('WARNING: Errors encountered while exctracting data')

def get_ticket_number():
    """Get TicketNumber from user and save it in the info folder."""
    global_vars['TicketNumber'] = None
    while global_vars['TicketNumber'] is None:
        _ticket = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([-_]?\w+|))$', _ticket):
            global_vars['TicketNumber'] = _ticket
            with open('{LogDir}\\TicketNumber'.format(**global_vars), 'w') as f:
                f.write(_ticket)

def human_readable_size(size, decimals=0):
    """Convert size in bytes to a human-readable format and return a str."""
    # Prep string formatting
    width = 3+decimals
    if decimals > 0:
        width += 1
    human_format = '>{width}.{decimals}f'.format(width=width, decimals=decimals)
    tmp = ''

    # Convert size to int
    try:
        size = int(size)
    except ValueError:
        size = convert_to_bytes(size)

    # Verify we have a valid size
    if size <= 0:
        return '{size:>{width}} b'.format(size='???', width=width)

    # Format string
    if size >= 1099511627776:
        size /= 1099511627776
        tmp = '{size:{human_format}} Tb'.format(size=size, human_format=human_format)
    elif size >= 1073741824:
        size /= 1073741824
        tmp = '{size:{human_format}} Gb'.format(size=size, human_format=human_format)
    elif size >= 1048576:
        size /= 1048576
        tmp = '{size:{human_format}} Mb'.format(size=size, human_format=human_format)
    elif size >= 1024:
        size /= 1024
        tmp = '{size:{human_format}} Kb'.format(size=size, human_format=human_format)
    else:
        tmp = '{size:{human_format}}  b'.format(size=size, human_format=human_format)

    # Return
    return tmp

def kill_process(name=None):
    """Kill any running caffeine.exe processes."""
    if name is None:
        raise Exception
    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()

def major_exception():
    """Display traceback and exit"""
    print_error('Major exception')
    print_warning('  Please let The Wizard know and he\'ll look into it (Please include the details below).')
    print(traceback.format_exc())
    print_log(traceback.format_exc())
    sleep(30)
    pause("Press Enter to exit...")
    sys.exit(1)

def menu_select(title='~ Untitled Menu ~', main_entries=[], action_entries=[],
    prompt='Please make a selection', secret_exit=False, disabled_label='DISABLED'):
    """Display options in a menu for user and return selected option as a str."""
    # Bail early
    if (len(main_entries) + len(action_entries) == 0):
        raise Exception("MenuError: No items given")

    # Build menu
    menu_splash =   '{title}\n\n'.format(title=title)
    width =         len(str(len(main_entries)))
    valid_answers = []
    if (secret_exit):
        valid_answers.append('Q')

    # Add main entries
    if (len(main_entries) > 0):
        for i in range(len(main_entries)):
            entry = main_entries[i]
            # Add Spacer
            if ('CRLF' in entry):
                menu_splash += '\n'
            if entry.get('Disabled', False):
                menu_splash += '{YELLOW}{number:>{width}}: {name} ({disabled}){CLEAR}\n'.format(
                    number =    i+1,
                    disabled =  disabled_label,
                    width =     width,
                    name =      entry.get('Display Name', entry['Name']),
                    **COLORS)
            else:
                valid_answers.append(str(i+1))
                menu_splash += '{number:>{width}}: {name}\n'.format(
                    number =    i+1,
                    width =     width,
                    name =      entry.get('Display Name', entry['Name']))
        menu_splash += '\n'

    # Add action entries
    if (len(action_entries) > 0):
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
        answer = input('{prompt}: '.format(prompt=prompt))

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

def popen_program(cmd=None, pipe=False, minimized=False, shell=False):
    """Run program and return a subprocess.Popen object."""
    if cmd is None:
        raise Exception('No program passed.')

    startupinfo=None
    if minimized:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 6

    if pipe:
        popen_obj = subprocess.Popen(cmd, shell=shell, startupinfo=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        popen_obj = subprocess.Popen(cmd, shell=shell, startupinfo=None)

    return popen_obj

def print_error(message='Generic error', end='\n', timestamp=True, **kwargs):
    """Prints message to screen in RED."""
    print('{RED}{message}{CLEAR}'.format(message=message, **COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_info(message='Generic info', end='\n', timestamp=True, **kwargs):
    """Prints message to screen in BLUE."""
    print('{BLUE}{message}{CLEAR}'.format(message=message, **COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_warning(message='Generic warning', end='\n', timestamp=True, **kwargs):
    """Prints message to screen in YELLOW."""
    print('{YELLOW}{message}{CLEAR}'.format(message=message, **COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_standard(message='Generic info', end='\n', timestamp=True, **kwargs):
    """Prints message to screen."""
    print('{message}'.format(message=message, **COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_success(message='Generic success', end='\n', timestamp=True, **kwargs):
    """Prints message to screen in GREEN."""
    print('{GREEN}{message}{CLEAR}'.format(message=message, **COLORS), end=end, **kwargs)
    print_log(message, end, timestamp)

def print_log(message='', end='\n', timestamp=True):
    if 'LogFile' in global_vars and global_vars['LogFile'] is not None:
        with open(global_vars['LogFile'], 'a') as f:
            for line in message.splitlines():
                f.write('{timestamp}{line}{end}'.format(
                    timestamp = time.strftime("%Y-%m-%d %H%M%z: ") if timestamp else '',
                    line =      line,
                    end =       end))

def run_program(cmd=None, args=[], check=True, pipe=True, shell=False):
    """Run program and return a subprocess.CompletedProcess object."""
    if cmd is None:
        raise Exception('No program passed.')

    _cmd = cmd
    if len(args) > 0:
        # BAD Need to refactor all calls to run_program to only use cmd=X
        ## That way the cmd var is set the same as the real run() and Popen() calls
        _cmd = [cmd] + args
    if shell:
        _cmd = ' '.join(_cmd)

    if pipe:
        process_return = subprocess.run(_cmd, check=check, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        process_return = subprocess.run(_cmd, check=check, shell=shell)

    return process_return

def show_info(message='~Some message~', info='~Some info~', indent=8, width=32):
    print_standard('{indent}{message:<{width}}{info}'.format(indent=' '*indent, width=width, message=message, info=info))

def sleep(seconds=2):
    time.sleep(seconds)

def stay_awake():
    """Prevent the system from sleeping or hibernating."""
    # Bail if caffeine is already running
    for proc in psutil.process_iter():
        if proc.name() == 'caffeine.exe':
            return
    # Extract and run
    extract_item('caffeine', silent=True)
    try:
        popen_program(global_vars['Tools']['Caffeine'])
    except:
        print_error('ERROR: No caffeine available; please set the power setting to High Performace.')

def try_and_print(function=None, message='Trying...', cs='CS', ns='NS', other_results={},
    catch_all=True, indent=8, width=32, print_return=False, silent_function=True, *args, **kwargs):
    """Run function, print if successful or not, and return dict.

    other_results is in the form of {'Warning': {'ExceptionClassName': 'Result Message'}, 'Error': {'ExceptionClassName': 'Result Message'}}
        The the ExceptionClassNames will be additionally excepted conditions and the result string will be printed in the correct color.
    catch_all=False will result in unspecified exceptions being re-raised."""
    if function is None:
        raise Exception
    err = ''
    wrn_exceptions = other_results.get('Warning', {}).keys()
    wrn_exceptions = tuple(getattr(sys.modules[__name__], e) for e in wrn_exceptions)
    err_exceptions = other_results.get('Error', {}).keys()
    err_exceptions = tuple(getattr(sys.modules[__name__], e) for e in err_exceptions)
    wrn_results = other_results.get('Warning', {})
    err_results = other_results.get('Error', {})

    # Run function and catch errors
    print_standard('{indent}{message:<{width}}'.format(indent=' '*indent, message=message, width=width), end='', flush=True)
    try:
        out = function(*args, **kwargs)
        if print_return:
            print_standard(out[0], timestamp=False)
            for item in out[1:]:
                print_standard('{indent}{item}'.format(indent=' '*(indent+width), item=item))
        elif silent_function:
            print_success(cs, timestamp=False)
    except wrn_exceptions as e:
        _result = wrn_results.get(e.__class__.__name__, 'Warning')
        print_warning(_result, timestamp=False)
        err = e
    except err_exceptions as e:
        _result = err_results.get(e.__class__.__name__, 'Error')
        print_error(_result, timestamp=False)
        err = e
    except:
        print_error(ns, timestamp=False)
        err = traceback.format_exc()

    # Return or raise?
    if bool(err) and not catch_all:
        raise
    else:
        return {'CS': not bool(err), 'Error': err}

def upload_data(path=None, file=None):
    """Add CLIENT_INFO_SERVER to authorized connections and upload file."""
    extract_item('PuTTY', filter='WK.ppk psftp.exe', silent=True)
    
    # Authorize connection to the server
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\SimonTatham\PuTTY\SshHostKeys')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\SimonTatham\PuTTY\SshHostKeys', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'rsa2@22:{IP}'.format(**CLIENT_INFO_SERVER), 0, winreg.REG_SZ, CLIENT_INFO_SERVER['RegEntry'])

    # Write batch file
    with open('{TmpDir}\\psftp.batch'.format(**global_vars), 'w', encoding='ascii') as f:
        f.write('lcd "{path}"\n'.format(path=path))
        f.write('cd "{Share}"\n'.format(**CLIENT_INFO_SERVER))
        f.write('mkdir {TicketNumber}\n'.format(**global_vars))
        f.write('cd {TicketNumber}\n'.format(**global_vars))
        f.write('put "{file}"\n'.format(file=file))

    # Upload Info
    _cmd = [
        global_vars['Tools']['PuTTY-PSFTP'],
        '-noagent',
        '-i', '{BinDir}\\PuTTY\\WK.ppk'.format(**global_vars),
        '{User}@{IP}'.format(**CLIENT_INFO_SERVER),
        '-b', '{TmpDir}\\psftp.batch'.format(**global_vars)]
    run_program(_cmd)

def wait_for_process(name=None):
    """Wait for process by name."""
    if name is None:
        raise Exception
    _still_running = True
    while _still_running:
        sleep(1)
        _still_running = False
        for proc in psutil.process_iter():
            if re.search(r'^{name}'.format(name=name), proc.name(), re.IGNORECASE):
                _still_running = True
    sleep(1)

# global_vars functions
def init_global_vars():
    """Sets global variables based on system info."""
    print_info('Initializing')
    try:
        try_and_print(message='Checking .bin...',           function=find_bin, catch_all=False, cs='Done', ns='Error')
        try_and_print(message='Checking environment...',    function=set_common_vars, catch_all=False, cs='Done', ns='Error')
        try_and_print(message='Checking OS...',             function=check_os, catch_all=False, cs='Done', ns='Error')
        try_and_print(message='Checking tools...',          function=check_tools, catch_all=False, cs='Done', ns='Error')
        try_and_print(message='Creating folders...',        function=make_tmp_dirs, catch_all=False, cs='Done', ns='Error')
        try_and_print(message='Clearing collisions...',     function=clean_env_vars, catch_all=False, cs='Done', ns='Error')
    except:
        major_exception()

def check_os():
    _vars_os = {}
    # Query registry
    _reg_path = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
    for key in ['CSDVersion', 'CurrentBuild', 'CurrentBuildNumber', 'CurrentVersion', 'ProductName']:
        try:
            _vars_os[key] = winreg.QueryValueEx(_reg_path, key)[0]
            if key in ['CurrentBuild', 'CurrentBuildNumber']:
                _vars_os[key] = int(_vars_os[key])
        except ValueError:
            # Couldn't convert Build to int so this should return interesting results...
            _vars_os[key] = 0
        except:
            _vars_os[key] = 'Unknown'

    # Determine OS bit depth
    _vars_os['Arch'] = 32
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        _vars_os['Arch'] = 64

    # Determine OS Name
    _vars_os['Name'] = '{ProductName} {CSDVersion}'.format(**_vars_os)
    if _vars_os['CurrentBuild'] == 9600:
        _vars_os['Name'] += ' Update'
    if _vars_os['CurrentBuild'] == 10240:
        _vars_os['Name'] += ' Release 1507 "Threshold 1"'
    if _vars_os['CurrentBuild'] == 10586:
        _vars_os['Name'] += ' Release 1511 "Threshold 2"'
    if _vars_os['CurrentBuild'] == 14393:
        _vars_os['Name'] += ' Release 1607 "Redstone 1" / "Anniversary Update"'
    if _vars_os['CurrentBuild'] == 15063:
        _vars_os['Name'] += ' Release 1703 "Redstone 1" / "Creators Update"'
    _vars_os['Name'] = _vars_os['Name'].replace('Service Pack ', 'SP')
    _vars_os['Name'] = _vars_os['Name'].replace('Unknown Release', 'Release')
    _vars_os['Name'] = re.sub(r'\s+', ' ', _vars_os['Name'])
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
    # === 10 v???? "Redstone 3" "Fall Creators Update" ==
    # 6.3.?????

    # Determine OS version
    _os_name = '{Name} x{Arch}'.format(**_vars_os)
    if _vars_os['CurrentVersion'] == '6.0':
        _vars_os['Version'] = 'Vista'
        _os_name = _os_name + ' (very outdated)'
    elif _vars_os['CurrentVersion'] == '6.1':
        _vars_os['Version'] = '7'
        if _vars_os['CSDVersion'] == 'Service Pack 1':
            _os_name = _os_name + ' (outdated)'
        else:
            _os_name = _os_name + ' (very outdated)'
    elif _vars_os['CurrentVersion'] == '6.2':
        _vars_os['Version'] = '8'
        _os_name = _os_name + ' (very outdated)'
    elif _vars_os['CurrentVersion'] == '6.3':
        if int(_vars_os['CurrentBuildNumber']) <= 9600:
            _vars_os['Version'] = '8'
        elif int(_vars_os['CurrentBuildNumber']) >= 10240:
            _vars_os['Version'] = '10'
        if _vars_os['CurrentBuild'] == 9200:
            _os_name = _os_name + ' (very outdated)'
        elif _vars_os['CurrentBuild'] == 9600:
            _os_name = _os_name + ' (outdated)'
        elif _vars_os['CurrentBuild'] == 10240:
            _os_name = _os_name + ' (very outdated)'
        elif _vars_os['CurrentBuild'] == 10586:
            _os_name = _os_name + ' (outdated)'
        elif _vars_os['CurrentBuild'] == 14393:
            _os_name = _os_name + ' (outdated)'
        elif _vars_os['CurrentBuild'] == 15063:
            pass # Current Win10
        else:
            _os_name = _os_name + ' (unrecognized)'
    _vars_os['DisplayName'] = _os_name

    # Determine bootup type
    _vars_os['SafeMode'] = False
    if 'SAFEBOOT_OPTION' in global_vars['Env']:
        _vars_os['SafeMode'] = True

    # Ignore activation status if in Safe Mode
    if _vars_os['SafeMode']:
        _vars_os['Activation'] = 'Activation status unavailable in safe mode'
    else:
        _vars_os['Activation'] = 'Unknown'

    global_vars['OS'] = _vars_os

    # Update activation status
    update_windows_activation_status()

def check_tools():
    # Add tools to dict
    if global_vars['OS'].get('Arch', 32) == 64:
        global_vars['Tools'] = {k: v.get('64', v.get('32')) for (k, v) in TOOLS.items()}
    else:
        global_vars['Tools'] = {k: v.get('32') for (k, v) in TOOLS.items()}

    # Fix paths
    global_vars['Tools'] = {k: v.format(**global_vars) for (k, v) in global_vars['Tools'].items()}

def clean_env_vars():
    # This fixes an issue where both global_vars and global_vars['Env'] are expanded at the same time
    for key in global_vars.keys():
        global_vars['Env'].pop(key, None)

def find_bin():
    _wd = os.getcwd()
    _base = None
    while _base is None:
        if os.path.exists('.bin'):
            _base = os.getcwd()
            break
        if re.fullmatch(r'\w:\\', os.getcwd()):
            break
        os.chdir('..')
    os.chdir(_wd)
    if _base is None:
        raise BinNotFoundError
    global_vars['BaseDir'] = _base

def make_tmp_dirs():
    os.makedirs(global_vars['BackupDir'], exist_ok=True)
    os.makedirs(global_vars['LogDir'], exist_ok=True)
    os.makedirs(global_vars['TmpDir'], exist_ok=True)

def set_common_vars():
    global_vars['Date'] =               time.strftime("%Y-%m-%d")
    global_vars['Date-Time'] =          time.strftime("%Y-%m-%d_%H%M_%z")
    global_vars['Env'] =                os.environ.copy()

    global_vars['ArchivePassword'] =    ARCHIVE_PASSWORD
    global_vars['BinDir'] =             '{BaseDir}\\.bin'.format(**global_vars)
    global_vars['CBinDir'] =            '{BaseDir}\\.cbin'.format(**global_vars)
    global_vars['ClientDir'] =          '{SYSTEMDRIVE}\\WK'.format(**global_vars['Env'])
    global_vars['BackupDir'] =          '{ClientDir}\\Backups\\{Date}'.format(**global_vars)
    global_vars['LogDir'] =             '{ClientDir}\\Info\\{Date}'.format(**global_vars)
    global_vars['QuarantineDir'] =      '{ClientDir}\\Quarantine'.format(**global_vars)
    global_vars['TmpDir'] =             '{BinDir}\\tmp'.format(**global_vars)

# Browsers
def backup_browsers():
    functions = [
        backup_chromium,
        backup_chrome,
        backup_chrome_canary,
        backup_firefox,
        backup_internet_explorer,
        backup_opera,
        backup_opera_beta,
        backup_opera_dev]
    errors = False
    for function in functions:
        try:
            function()
        except NoProfilesError:
            pass
        except:
            errors = True
    if errors:
        raise GenericError

def backup_chromium():
    """Create backup of Chromium in the BackupDir."""
    if os.path.exists('{LOCALAPPDATA}\\Chromium\\User Data'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Chromium.7z'.format(**global_vars, **global_vars['Env']),
            '{LOCALAPPDATA}\\Chromium\\User Data'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_chrome():
    """Create backup of Google Chrome in the BackupDir."""
    if os.path.exists('{LOCALAPPDATA}\\Google\\Chrome\\User Data'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Google Chrome.7z'.format(**global_vars, **global_vars['Env']),
            '{LOCALAPPDATA}\\Google\\Chrome\\User Data'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_chrome_canary():
    """Create backup of Google Chrome Canary in the BackupDir."""
    if os.path.exists('{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Google Chrome Canary.7z'.format(**global_vars, **global_vars['Env']),
            '{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_internet_explorer():
    """Create backup of Internet Explorer in the BackupDir."""
    run_program('reg export "hkcu\\Software\\Microsoft\\Internet Explorer" "{TmpDir}\\Internet Explorer (HKCU).reg" /y'.format(**global_vars), check=False)
    run_program('reg export "hklm\\Software\\Microsoft\\Internet Explorer" "{TmpDir}\\Internet Explorer (HKLM).reg" /y'.format(**global_vars), check=False)
    cmd = [
        global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
        '{BackupDir}\\Browsers ({USERNAME})\\Internet Explorer.7z'.format(**global_vars, **global_vars['Env']),
        '{TmpDir}\\Internet*.reg'.format(**global_vars),
        '{USERPROFILE}\\Favorites'.format(**global_vars['Env'])]
    run_program(cmd, check=False)

def backup_firefox():
    """Create backup of Mozilla Firefox in the BackupDir."""
    if os.path.exists('{APPDATA}\\Mozilla\\Firefox'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Mozilla Firefox.7z'.format(**global_vars, **global_vars['Env']),
            '{APPDATA}\\Mozilla\\Firefox\\Profile*'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_opera():
    """Create backup of Opera Chromium in the BackupDir."""
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Stable'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Opera.7z'.format(**global_vars, **global_vars['Env']),
            '{APPDATA}\\Opera Software\\Opera Stable'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_opera_beta():
    """Create backup of Opera Chromium Beta in the BackupDir."""
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Next'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Opera Beta.7z'.format(**global_vars, **global_vars['Env']),
            '{APPDATA}\\Opera Software\\Opera Next'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def backup_opera_dev():
    """Create backup of Opera Chromium Developer in the BackupDir."""
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Developer'.format(**global_vars['Env'])):
        cmd = [
            global_vars['Tools']['SevenZip'], 'a', '-aoa', '-bso0', '-bse0', '-mx=1',
            '{BackupDir}\\Browsers ({USERNAME})\\Opera Dev.7z'.format(**global_vars, **global_vars['Env']),
            '{APPDATA}\\Opera Software\\Opera Developer'.format(**global_vars['Env'])]
        run_program(cmd, check=False)
    else:
        raise NoProfilesError

def clean_chromium_profile(profile):
    """Renames profile folder as backup and then recreates the folder with only the essential files."""
    if profile is None:
        raise Exception
    # print_info('    Resetting profile: {name}'.format(name=profile.name))
    backup_path = '{path}_{Date}.bak'.format(path=profile.path, **global_vars)
    backup_path = non_clobber_rename(backup_path)
    shutil.move(profile.path, backup_path)
    os.makedirs(profile.path, exist_ok=True)

    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_CHROMIUM_ITEMS.search(entry.name):
            shutil.copy(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))

def clean_internet_explorer():
    """Uses the built-in function to reset IE and sets the homepage."""
    kill_process('iexplore.exe')
    run_program('rundll32.exe', ['inetcpl.cpl,ResetIEtoDefaults'], check=False)
    key = r'Software\Microsoft\Internet Explorer\Main'

    # Set homepage
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'Start Page', 0, winreg.REG_SZ, DEFAULT_HOMEPAGE)
        try:
            winreg.DeleteValue(_key, 'Secondary Start Pages')
        except FileNotFoundError:
            pass

def clean_firefox_profile(profile):
    """Renames profile folder as backup and then recreates the folder with only the essential files."""
    if profile is None:
        raise Exception
    # print_info('    Resetting profile: {name}'.format(name=profile.name))
    backup_path = '{path}_{Date}.bak'.format(path=profile.path, **global_vars)
    backup_path = non_clobber_rename(backup_path)
    shutil.move(profile.path, backup_path)
    homepages = []
    os.makedirs(profile.path, exist_ok=True)

    # Restore essential files from backup_path
    for entry in os.scandir(backup_path):
        if REGEX_FIREFOX.search(entry.name):
            if entry.is_dir():
                shutil.copytree(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))
            else:
                shutil.copy(entry.path, '{path}\\{name}'.format(path=profile.path, name=entry.name))

    # Set profile defaults
    with open('{path}\\prefs.js'.format(path=profile.path), 'a', encoding='ascii') as f:
        f.write('user_pref("browser.search.geoSpecificDefaults", false);\n')

        # Set search to Google
        f.write('user_pref("browser.search.defaultenginename", "Google");\n')
        f.write('user_pref("browser.search.defaultenginename.US", "Google");\n')

        # Set homepage
        f.write('user_pref("browser.startup.homepage", "{homepage}");\n'.format(homepage=DEFAULT_HOMEPAGE))

def config_internet_explorer():
    ie_exe = get_iexplorer_exe()
    run_program(ie_exe, ['https://www.microsoft.com/en-us/iegallery'], check=False)

def config_google_chrome():
    chrome_exe = get_chrome_exe()
    if chrome_exe is None:
        raise NotInstalledError

    # Check for system exensions
    _ublock_origin = None
    _ublock_extra = None
    try:
        _ublock_origin = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE, r'Software\Wow6432Node\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm')
    except FileNotFoundError:
        pass
    try:
        _ublock_extra = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE, r'Software\Wow6432Node\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco')
    except FileNotFoundError:
        pass

    # Open Chrome
    _args = [
        'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en',
        'https://chrome.google.com/webstore/detail/ublock-origin-extra/pgdnlhfefecpicbbihgmbmffkjpaplco?hl=en']
    if _ublock_origin is None and _ublock_extra is None:
        run_program(chrome_exe, _args, check=False)
    elif _ublock_origin is None:
        run_program(chrome_exe, [_args[0]], check=False)
    elif _ublock_extra is None:
        run_program(chrome_exe, [_args[1]], check=False)
    else:
        run_program(chrome_exe, ['chrome://extensions'], check=False)

def config_google_chrome_canary():
    chrome_canary_exe = get_chrome_canary_exe()
    if chrome_canary_exe is None:
        raise NotInstalledError
    _args = [
        'https://chrome.google.com/webstore/detail/ublock-origin/cjpalhdlnbpafiamejdnhcphjbkeiagm?hl=en',
        'https://chrome.google.com/webstore/detail/ublock-origin-extra/pgdnlhfefecpicbbihgmbmffkjpaplco?hl=en']
    run_program(chrome_canary_exe, _args, check=False)

def config_mozilla_firefox():
    firefox_exe = get_firefox_exe()
    if firefox_exe is None:
        raise NotInstalledError

    # Check for system extension(s)
    _ublock_origin = '{PROGRAMFILES}\\Mozilla Firefox\\distribution\\extensions\\uBlock0@raymondhill.net'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        _ublock_origin = '{PROGRAMFILES(X86)}\\Mozilla Firefox\\distribution\\extensions\\uBlock0@raymondhill.net'.format(**global_vars['Env'])

    # Open Firefox
    if os.path.exists(_ublock_origin):
        run_program(firefox_exe, ['about:addons'], check=False)
    else:
        run_program(firefox_exe, ['https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'], check=False)

def config_mozilla_firefox_dev():
    firefox_dev_exe = get_firefox_dev_exe()
    if firefox_dev_exe is None:
        raise NotInstalledError
    run_program(firefox_dev_exe, ['https://addons.mozilla.org/en-us/firefox/addon/ublock-origin/'], check=False)

def config_opera():
    opera_exe = get_opera_exe()
    if opera_exe is None:
        raise NotInstalledError
    run_program(opera_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)

def config_opera_beta():
    opera_beta_exe = get_opera_beta_exe()
    if opera_beta_exe is None:
        raise NotInstalledError
    run_program(opera_beta_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)

def config_opera_dev():
    opera_dev_exe = get_opera_dev_exe()
    if opera_dev_exe is None:
        raise NotInstalledError
    run_program(opera_dev_exe, ['https://addons.opera.com/en/extensions/details/ublock/?display=en'], check=False)

def create_firefox_default_profiles():
    """Create new default profile for Mozilla Firefox for both stable and dev releases."""
    firefox_exe = get_firefox_exe()
    firefox_dev_exe = get_firefox_dev_exe()
    profiles_ini_path = '{APPDATA}\\Mozilla\\Firefox\\profiles.ini'.format(**global_vars['Env'])

    # Rename profiles.ini
    if os.path.exists(profiles_ini_path):
        backup_path = '{path}_{Date}.bak'.format(path=profiles_ini_path, **global_vars)
        backup_path = non_clobber_rename(backup_path)
        shutil.move(profiles_ini_path, backup_path)

    # Create profile(s)
    if firefox_exe is not None:
        run_program(firefox_exe, ['-createprofile', 'default'], check=False)
    if firefox_dev_exe is not None:
        run_program(firefox_dev_exe, ['-createprofile'], check=False)

def get_chrome_exe():
    """Check for conflicting Chrome installations and return chrome.exe path as str."""
    install_multi = '{PROGRAMFILES}\\Google\\Chrome\\Application\\chrome.exe'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        install_multi = '{PROGRAMFILES(X86)}\\Google\\Chrome\\Application\\chrome.exe'.format(**global_vars['Env'])
    install_single = '{LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe'.format(**global_vars['Env'])
    if os.path.exists(install_multi):
        if os.path.exists(install_single):
            print_log('    WARNING: Single-user and multi-user installations present.')
            print_log('             It is recommended to move to only having the multi-user installation.')
        return install_multi
    elif os.path.exists(install_single):
        return install_single
    else:
        return None

def get_chrome_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{LOCALAPPDATA}\\Google\\Chrome\\User Data'.format(**global_vars['Env'])):
            if entry.is_dir() and re.search(r'^(Default|Profile)', entry.name, re.IGNORECASE):
                profiles.append(entry)
        profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    except:
        pass

    return profiles

def get_chrome_canary_exe():
    """Check for Google Chrome Canary installation and return chrome.exe path as str."""
    prog_exe = '{LOCALAPPDATA}\\Google\\Chrome SxS\\Application\\chrome.exe'.format(**global_vars['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_chrome_canary_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{LOCALAPPDATA}\\Google\\Chrome SxS\\User Data'.format(**global_vars['Env'])):
            if entry.is_dir() and re.search(r'^(Default|Profile)', entry.name, re.IGNORECASE):
                profiles.append(entry)
        profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    except:
        pass

    return profiles

def get_iexplorer_exe():
    """Find and return iexplorer.exe path as str."""
    ie_exe = '{PROGRAMFILES}\\Internet Explorer\\iexplore.exe'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        ie_exe = '{PROGRAMFILES(X86)}\\Internet Explorer\\iexplore.exe'.format(**global_vars['Env'])
    return ie_exe

def get_firefox_exe():
    """Check for Mozilla Firefox installation and return firefox.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Mozilla Firefox\\firefox.exe'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Mozilla Firefox\\firefox.exe'.format(**global_vars['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_firefox_dev_exe():
    """Check for Mozilla Firefox Developer Edition installation and return firefox.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Firefox Developer Edition\\firefox.exe'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Firefox Developer Edition\\firefox.exe'.format(**global_vars['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_firefox_profiles():
    """Find any existing Chrome profiles and return as a list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{APPDATA}\\Mozilla\\Firefox\\Profiles'.format(**global_vars['Env'])):
            if entry.is_dir():
                profiles.append(entry)
        profiles = [p for p in profiles if not re.search(r'\.(wk|)bak.*', p.name, re.IGNORECASE)]
    except:
        pass

    return profiles

def get_opera_exe():
    """Check for Opera installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera\\launcher.exe'.format(**global_vars['Env'])
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        prog_exe = '{PROGRAMFILES(X86)}\\Opera\\launcher.exe'.format(**global_vars['Env'])
    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_beta_exe():
    """Check for Opera Beta installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera beta\\launcher.exe'.format(**global_vars['Env'])
    # Installs as 64-bit on a 64-bit OS so PROGRAMFILES should always be correct

    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_dev_exe():
    """Check for Opera Beta installation and return launcher.exe path as str."""
    prog_exe = '{PROGRAMFILES}\\Opera developer\\launcher.exe'.format(**global_vars['Env'])
    # Installs as 64-bit on a 64-bit OS so PROGRAMFILES should always be correct

    if os.path.exists(prog_exe):
        return prog_exe
    else:
        return None

def get_opera_profile():
    """Find an existing Opera profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{APPDATA}\\Opera Software'.format(**global_vars['Env'])):
            if entry.is_dir() and entry.name == 'Opera Stable':
                return [entry]
    except:
        pass

    return profiles

def get_opera_beta_profile():
    """Find an existing Opera Beta profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{APPDATA}\\Opera Software'.format(**global_vars['Env'])):
            if entry.is_dir() and entry.name == 'Opera Next':
                return [entry]
    except:
        pass

    return profiles

def get_opera_dev_profile():
    """Find an existing Opera Dev profile and return as a length-1 list of os.DirEntry objects."""
    profiles = []
    try:
        for entry in os.scandir('{APPDATA}\\Opera Software'.format(**global_vars['Env'])):
            if entry.is_dir() and entry.name == 'Opera Developer':
                return [entry]
    except:
        pass

    return profiles

def list_homepages(indent=8, width=32):
    """List current homepages for reference."""
    print_standard('{indent}{browser:<{width}}'.format(indent=' '*indent, width=width, browser='Google Chrome...'), end='', flush=True)
    print_warning('Currently not possible', timestamp=False)

    # Firefox
    profiles = get_firefox_profiles()
    if len(profiles) > 0:
        print_standard('{indent}{browser:<{width}}'.format(indent=' '*indent, width=width, browser='Mozilla Firefox...'))

    for profile in profiles:
        homepages = []
        try:
            with open('{path}\\prefs.js'.format(path=profile.path), 'r') as f:
                _search = re.search(r'browser\.startup\.homepage", "([^"]*)"', f.read(), re.IGNORECASE)
                if _search:
                    homepages = _search.group(1).split('|')
        except FileNotFoundError:
            pass

        for page in homepages:
            print_standard('{indent}{name:<{width}}{page}'.format(indent=' '*(indent+4), width=width-4, name=profile.name, page=page))

    # IE
    homepage = ''
    secondary_homepages = []
    key = r'Software\Microsoft\Internet Explorer\Main'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as _key:
        homepage = winreg.QueryValueEx(_key, 'Start Page')[0]
        try:
            secondary_homepages = winreg.QueryValueEx(_key, 'Secondary Start Pages')[0]
        except FileNotFoundError:
            pass
    print_standard('{indent}{browser:<{width}}{page}'.format(indent=' '*indent, width=width, browser='Internet Explorer...', page=homepage))
    for page in secondary_homepages:
        print_standard('{indent}{page}'.format(indent=' '*(indent+width), page=page))

def reset_google_chrome():
    kill_process('chrome.exe')
    chrome_exe = get_chrome_exe()
    profiles = get_chrome_profiles()
    if len(profiles) == 0:
        raise NoProfilesError

    for profile in profiles:
        clean_chromium_profile(profile)

def reset_google_chrome_canary():
    kill_process('chrome.exe')
    chrome_canary_exe = get_chrome_canary_exe()
    profiles = get_chrome_canary_profiles()
    if len(profiles) == 0:
        raise NoProfilesError

    for profile in profiles:
        clean_chromium_profile(profile)

def reset_mozilla_firefox():
    kill_process('firefox.exe')
    profiles = get_firefox_profiles()

    if len(profiles) == 0:
        create_firefox_default_profiles()
        kill_process('firefox.exe')
        raise NoProfilesError
    else:
        for profile in profiles:
            clean_firefox_profile(profile)

def reset_opera():
    kill_process('opera.exe')
    opera_exe = get_opera_exe()
    profiles = get_opera_profile()
    if len(profiles) == 0:
        raise NoProfilesError

    # Reset browser (Opera only supports one profile)
    clean_chromium_profile(profiles[0])

def reset_opera_beta():
    kill_process('opera.exe')
    opera_beta_exe = get_opera_beta_exe()
    profiles = get_opera_beta_profile()
    if len(profiles) == 0:
        raise NoProfilesError

    # Reset browser (Opera only supports one profile)
    clean_chromium_profile(profiles[0])

def reset_opera_dev():
    kill_process('opera.exe')
    opera_dev_exe = get_opera_dev_exe()
    profiles = get_opera_dev_profile()
    if len(profiles) == 0:
        raise NoProfilesError

    # Reset browser (Opera only supports one profile)
    clean_chromium_profile(profiles[0])

def set_chrome_as_default():
    chrome_exe = get_chrome_exe()
    if chrome_exe is None:
        raise NotInstalledError
    run_program(chrome_exe, ['--make-default-browser'], check=False)
    if global_vars['OS']['Version'] in ['10']:
        popen_program('ms-settings:defaultapps')

# Cleanup
def cleanup_adwcleaner():
    _path = '{SYSTEMDRIVE}\\AdwCleaner'.format(**global_vars['Env'])
    if os.path.exists(_path):
        os.makedirs('{ClientDir}\\Info'.format(**global_vars), exist_ok=True)
        for entry in os.scandir(_path):
            if entry.is_file() and re.search(r'*.(log|txt)', entry.name):
                _name = re.sub(r'^(.*)\.', '\1_{Date-Time}'.format(**global_vars), entry.name, re.IGNORECASE)
                _name = '{ClientDir}\\Info\\{name}'.format(name=_name, **global_vars)
                shutil.move(entry.path, non_clobber_rename(_name))
            elif entry.name == 'Quarantine':
                os.makedirs(global_vars['QuarantineDir'], exist_ok=True)
                _name = '{QuarantineDir}\\AdwCleaner_{Date-Time}'.format(**global_vars)
                shutil.move(entry.path, non_clobber_rename(_name))
        shutil.rmtree(_path)

def cleanup_desktop():
    os.makedirs('{ClientDir}\\Info'.format(**global_vars), exist_ok=True)
    if os.path.exists('{USERPROFILE}\\Desktop'.format(**global_vars['Env'])):
        for entry in os.scandir('{USERPROFILE}\\Desktop'.format(**global_vars['Env'])):
            # JRT, RKill, Shortcut cleaner
            if re.search(r'^((JRT|RKill).*|sc-cleaner)', entry.name, re.IGNORECASE):
                _name = '{ClientDir}\\Info\\{name}'.format(name=entry.name, **global_vars)
                shutil.move(entry.path, non_clobber_rename(_name))
    run_program('rmdir "{path}"'.format(path='{ClientDir}\\Info'.format(**global_vars)), check=False, shell=True)

def uninstall_eset():
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        _path = '{PROGRAMFILES(X86)}\\ESET'.format(**global_vars['Env'])
    else:
        _path = '{PROGRAMFILES}\\ESET'.format(**global_vars['Env'])
    if os.path.exists('{path}\\ESET Online Scanner'.format(path=_path)):
        run_program('"{path}\\ESET Online Scanner\\OnlineScannerUninstaller.exe" -s'.format(path=_path))
        shutil.rmtree('{path}\\ESET Online Scanner'.format(path=_path))
        run_program('rmdir "{path}"'.format(path=_path), check=False)

def uninstall_mbam():
    # if 'PROGRAMFILES(X86)' in global_vars['Env']:
        # _path = '{PROGRAMFILES(X86)}\\Malwarebytes Anti-Malware'.format(**global_vars['Env'])
    # else:
        # _path = '{PROGRAMFILES}\\Malwarebytes Anti-Malware'.format(**global_vars['Env'])
    # if os.path.exists('{path}'.format(path=_path)):
        # print_warning('* Malwarebytes Anti-Malware installed.')
        # if ask('  Uninstall?'):
            # try:
                # run_program('"{path}\\unins000.exe" /SILENT'.format(path=_path))
                # run_program('rmdir "{path}"'.format(path=_path), check=False)
            # except:
                # print_error('ERROR: Failed to uninstall Malwarebytes Anti-Malware.')
    pass

def uninstall_sas():
    # It is always in programfiles (not x86) ??
    _path = '{PROGRAMFILES}\\SUPERAntiSpyware'.format(**global_vars['Env'])
    if os.path.exists(_path):
        run_program('{path}\\Uninstall.exe'.format(path=_path))
        run_program('rmdir "{path}"'.format(path=_path), check=False)

# Config
def config_classicstart():
    # User level, not system level
    _classicstart = '{PROGRAMFILES}\\Classic Shell\\ClassicStartMenu.exe'.format(**global_vars['Env'])
    _skin = '{PROGRAMFILES}\\Classic Shell\\Skins\\Metro-Win10-Black.skin7'.format(**global_vars['Env'])
    extract_item('ClassicStartSkin', silent=True)

    # Stop Classic Start
    run_program([_classicstart, '-exit'], check=False)

    # Configure
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\IvoSoft\ClassicShell\Settings')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\IvoSoft\ClassicStartMenu\MRU')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\IvoSoft\ClassicStartMenu\Settings')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\IvoSoft\ClassicStartMenu', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'ShowedStyle2', 0, winreg.REG_DWORD, 1)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\IvoSoft\ClassicStartMenu\Settings', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'MenuStyle', 0, winreg.REG_SZ, 'Win7')
        winreg.SetValueEx(_key, 'RecentPrograms', 0, winreg.REG_SZ, 'Recent')
        winreg.SetValueEx(_key, 'SkipMetro', 0, winreg.REG_DWORD, 1)

        # Enable Win10 theme if on Win10
        if global_vars['OS']['Version'] == '10' and os.path.exists(_skin):
            winreg.SetValueEx(_key, 'SkinW7', 0, winreg.REG_SZ, 'Metro-Win10-Black')
            winreg.SetValueEx(_key, 'SkinVariationW7', 0, winreg.REG_SZ, '')

    # Pin Google Chrome to Start Menu (Classic)
    _source = '{BinDir}\\ClassicStartSkin\\Google Chrome.lnk'.format(**global_vars)
    _dest_path = '{APPDATA}\\ClassicShell\\Pinned'.format(**global_vars['Env'])
    _dest = '{dest_path}\\Google Chrome.lnk'.format(dest_path=_dest_path)
    try:
        os.makedirs(_dest_path, exist_ok=True)
        shutil.copy(_source, _dest)
    except:
        pass # Meh, it's fine without

    # (Re)start Classic Start
    run_program([_classicstart, '-exit'], check=False)
    sleep(1)
    kill_process('ClassicStartMenu.exe')
    run_program(_classicstart, check=False)

def config_explorer_system():
    # Disable Telemetry
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection', 0, winreg.KEY_WRITE)
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\DataCollection', 0, winreg.KEY_WRITE)
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY)
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'AllowTelemetry', 0, winreg.REG_DWORD, 0)
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Policies\Microsoft\Windows\DataCollection', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'AllowTelemetry', 0, winreg.REG_DWORD, 0)
    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY) as _key:
        winreg.SetValueEx(_key, 'AllowTelemetry', 0, winreg.REG_DWORD, 0)

    # Disable Wi-Fi Sense
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\PolicyManager\default\WiFi\AllowWiFiHotSpotReporting', 0, winreg.KEY_WRITE)
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\PolicyManager\default\WiFi\AllowAutoConnectToWiFiSenseHotspots', 0, winreg.KEY_WRITE)
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\PolicyManager\default\WiFi\AllowWiFiHotSpotReporting', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'Value', 0, winreg.REG_DWORD, 0)
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\PolicyManager\default\WiFi\AllowAutoConnectToWiFiSenseHotspots', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'Value', 0, winreg.REG_DWORD, 0)

    # Disable Location Tracking
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Sensor\Overrides\{BFA794E4-F964-4FDB-90F6-51056BFE4B44}', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'SensorPermissionState', 0, winreg.REG_DWORD, 0)
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'System\CurrentControlSet\Services\lfsvc\Service\Configuration', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'Status', 0, winreg.REG_DWORD, 0)

def config_explorer_user():
    # Disable Cortana
    winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Personalization\Settings', 0, winreg.KEY_WRITE)
    winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\InputPersonalization', 0, winreg.KEY_WRITE)
    winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\InputPersonalization\TrainedDataStore', 0, winreg.KEY_WRITE)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Personalization\Settings', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'AcceptedPrivacyPolicy', 0, winreg.REG_DWORD, 0)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\InputPersonalization', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'RestrictImplicitTextCollection', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'RestrictImplicitInkCollection', 0, winreg.REG_DWORD, 1)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\InputPersonalization\TrainedDataStore', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'HarvestContacts', 0, winreg.REG_DWORD, 1)

    # Hide Search button / box
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Search', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'SearchboxTaskbarMode', 0, winreg.REG_DWORD, 0)

    # Change default Explorer view to "Computer"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'LaunchTo', 0, winreg.REG_DWORD, 1)

def update_clock():
    # Set Timezone and sync clock
    run_program('tzutil /s "Pacific Standard Time"', check=False)
    run_program('net stop w32ime', check=False)
    run_program('w32tm /config /syncfromflags:manual /manualpeerlist:"us.pool.ntp.org time.nist.gov time.windows.com"', check=False)
    run_program('net start w32ime', check=False)
    run_program('w32tm /resync /nowait', check=False)

# Disk Management and Data Transfers
def cleanup_transfer():
    """Fix permissions and walk through transfer folder (from the bottom) and remove extraneous items."""
    cmd = ['attrib', '-a', '-h', '-r', '-s', global_vars['Data']['Destination']]
    run_program(cmd, check=False)
    try:
        os.rmdir(global_vars['Data']['Destination'])
    except:
        pass # Should only remove when empty
    if os.path.exists(global_vars['Data']['Destination']):
        for root, dirs, files in os.walk(global_vars['Data']['Destination'], topdown=False):
            for name in dirs:
                # Remove empty directories and junction points
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
            for name in files:
                # Remove files based on exclusion regex
                if REGEX_EXCL_ITEMS.search(name):
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass

def extract_keys():
    """Extract keys from provided hives and return a dict."""
    keys = {}

    # Extract keys
    extract_item('ProduKey', silent=True)
    for hive in find_software_hives():
        _cmd = [
            global_vars['Tools']['ProduKey'],
            '/IEKeys', '0',
            '/WindowsKeys', '1',
            '/OfficeKeys', '1',
            '/ExtractEdition', '1',
            '/nosavereg',
            '/regfile', hive,
            '/scomma', '']
        _out = run_program(_cmd)

        for line in _out.stdout.decode().splitlines():
            # Add key to keys under product only if unique
            _tmp = line.split(',')
            _product = _tmp[0]
            _key = _tmp[2]
            if _product not in keys:
                keys[_product] = []
            if _key not in keys[_product]:
                keys[_product].append(_key)

    global_vars['Keys'] = keys

def is_valid_wim_image(item):
    _valid = bool(item.is_file() and REGEX_WIM_FILE.search(item.name))
    if _valid:
        extract_item('wimlib', silent=True)
        try:
            _cmd = [global_vars['Tools']['wimlib-imagex'], 'info', item.path]
            run_program(_cmd)
        except subprocess.CalledProcessError:
            _valid = False
            print_log('WARNING: Image "{image}" damaged.'.format(image=item.name))
    return _valid

def mount_backup_shares():
    """Mount the backup shares unless labeled as already mounted."""
    for server in BACKUP_SERVERS:
        # Blindly skip if we mounted earlier
        if server['Mounted']:
            continue
        else:
            try:
                # Test connection
                ping_test(server['IP'])

                # Mount
                run_program('net use \\\\{IP}\\{Share} /user:{User} {Pass}'.format(**server))
                print_info('Mounted {Name}'.format(**server))
                server['Mounted'] = True
            except subprocess.CalledProcessError:
                print_error('Failed to mount \\\\{Name}\\{Share}, {IP} unreachable.'.format(**server))
                sleep(1)
            except:
                print_warning('Failed to mount \\\\{Name}\\{Share} ({IP})'.format(**server))
                sleep(1)

def run_fast_copy(items=None, dest=None):
    if items is None or dest is None:
        raise Exception
    elif len(items) == 0:
        raise Exception

    cmd = [global_vars['Tools']['FastCopy'], *FAST_COPY_ARGS]
    if 'LogFile' in global_vars:
        cmd.append('/logfile={LogFile}'.format(**global_vars))
    cmd.extend(items)
    cmd.append('/to={dest}\\'.format(dest=dest))
    run_program(cmd)

def run_wimextract(source=None, items=None, dest=None):
    if source is None or items is None or dest is None:
        raise Exception
    elif len(items) == 0:
        raise Exception
    extract_item('wimlib', silent=True)

    # Write files.txt
    with open('{TmpDir}\\wim_files.txt'.format(**global_vars), 'w') as f:
        # Defaults
        for item in items:
            f.write('{item}\n'.format(item=item))
    sleep(1) # For safety?

    # Extract files
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'extract',
        source, '1',
        '@{TmpDir}\\wim_files.txt'.format(**global_vars),
        '--dest-dir={dest}\\'.format(dest=dest),
        '--no-acls',
        '--nullglob']
    run_program(cmd)

def save_keys():
    key_list = []
    if global_vars['Keys']:
        for product in sorted(global_vars['Keys']):
            key_list.append(product)
            for key in sorted(global_vars['Keys'][product]):
                key_list.append('  {key}'.format(key=key))
    else:
        key_list.append('No keys found.')

    return key_list

def scan_backup():
    if 'Source' not in global_vars['Data']:
        raise Exception
    backup = global_vars['Data']['Source']
    global_vars['Data']['Selected Items'] = []

    if backup.is_dir():
        # File-Based
        print_standard('Scanning File-Based backup: {}'.format(backup.path))
        scan_backup_folder(backup)
    else:
        # Image-Based
        if REGEX_WIM_FILE.search(backup.name):
            print_standard('Scanning Image-Based backup: {}'.format(backup.path))
            selected_items = scan_backup_wim(backup)
        else:
            print_error('ERROR: Unsupported image: {}'.format(backup.path))
            raise GenericError

def scan_backup_folder(backup_folder=None, rel_path=None, interactive=True):
    if backup_folder is None:
        raise Exception
    win_olds = []
    dest = '{dest}{rel_path}'.format(
        dest = global_vars['Data']['Destination'],
        rel_path = '' if rel_path is None else '\\'+rel_path)

    # Root items
    _items = []
    for item in os.scandir(backup_folder.path):
        if REGEX_INCL_ROOT_ITEMS.search(item.name):
            _items.append(item.path)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item.name):
            if (not interactive
                or ask('Copy: "{rel_path}{name}" ?'.format(name=item.name, rel_path='' if rel_path is None else rel_path+'\\'))):
                _items.append(item.path)
        if REGEX_WINDOWS_OLD.search(item.name):
            win_olds.append(item)
    if len(_items) > 0:
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Root Items...'.format('' if rel_path is None else rel_path+'\\'),
            'Items':        _items.copy(),
            'Destination':  dest})

    # Fonts
    if os.path.exists('{}\\Windows\\Fonts'.format(backup_folder.path)):
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Fonts...'.format('' if rel_path is None else rel_path+'\\'),
            'Items':        ['{}\\Windows\\Fonts'.format(backup_folder.path)],
            'Destination':  '{}\\{}'.format(dest, 'Windows')})
        _items.append('{source}\\Windows\\Fonts'.format(source=backup_folder.path))

    # Registry
    _items = []
    if os.path.exists('{}\\Windows\\System32\\config'.format(backup_folder.path)):
        _items.append('{}\\Windows\\System32\\config'.format(backup_folder.path))
    if os.path.exists('{}\\Windows\\System32\\OEM'.format(backup_folder.path)):
        _items.append('{}\\Windows\\System32\\OEM'.format(backup_folder.path))
    if len(_items) > 0:
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Registry...'.format('' if rel_path is None else rel_path+'\\'),
            'Items':        _items.copy(),
            'Destination':  '{}\\{}'.format(dest, 'Windows\\System32')})

    # Windows.old(s)
    for old in win_olds:
        scan_backup_folder(old.path, rel_path=old.name, interactive=False)

def scan_backup_wim(backup_file=None, rel_path=None, interactive=True):
    if backup_file is None:
        raise Exception
    if rel_path is None:
        rel_path = ''
    else:
        rel_path = rel_path + '\\'
    win_olds = []

    # Scan source
    extract_item('wimlib', silent=True)
    _cmd = [
        global_vars['Tools']['wimlib-imagex'], 'dir',
        backup_file.path, '1']
    try:
        _list = run_program(_cmd)
    except subprocess.CalledProcessError as err:
        print_error('ERROR: Failed to get file list.')
        raise

    # Root Items
    _items = []
    root_items = [i.strip() for i in _list.stdout.decode('utf-8', 'ignore').splitlines() if i.count('\\') == 1 and i.strip() != '\\']
    if rel_path:
        root_items = [i.replace(rel_path, '') for i in root_items if rel_path in i]
    for item in root_items:
        if REGEX_INCL_ROOT_ITEMS.search(item):
            _items.append(item)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item):
            if (not interactive
                or ask('Extract: "{rel_path}{name}" ?'.format(name=item, rel_path=rel_path))):
                _items.append('{}{}'.format(rel_path, item))
        if REGEX_WINDOWS_OLD.search(item):
            win_olds.append(item)
    if len(_items) > 0:
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Root Items...'.format(rel_path),
            'Items':        _items.copy(),
            'Destination':  global_vars['Data']['Destination']})

    # Fonts
    if wim_contains(backup_file.path, '{}Windows\\Fonts'.format(rel_path)):
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Fonts...'.format(rel_path),
            'Items':        ['{}\\Windows\\Fonts'.format(rel_path)],
            'Destination':  global_vars['Data']['Destination']})

    # Registry
    _items = []
    if wim_contains(backup_file.path, '{}Windows\\System32\\config'.format(rel_path)):
        _items.append('{}Windows\\System32\\config'.format(rel_path))
    if wim_contains(backup_file.path, '{}Windows\\System32\\OEM'.format(rel_path)):
        _items.append('{}Windows\\System32\\OEM'.format(rel_path))
    if len(_items) > 0:
        global_vars['Data']['Selected Items'].append({
            'Message': '{}Registry...'.format(rel_path),
            'Items':        _items.copy(),
            'Destination':  global_vars['Data']['Destination']})

    # Windows.old(s)
    for old in win_olds:
        scan_backup_wim(backup_file, rel_path=old, interactive=False)

def select_backup():
    """Select backup from those found on the BACKUP_SERVERS for the ticket."""
    sources = []
    mount_backup_shares()

    # Check for ticket folders on servers
    for server in BACKUP_SERVERS:
        if server['Mounted']:
            print_standard('Scanning {server}...'.format(server=server['Name']))
            for d in os.scandir('\\\\{IP}\\{Share}'.format(**server)):
                if d.is_dir() and re.match('^{}'.format(global_vars['TicketNumber']), d.name):
                    # Add folder to sources
                    sources.append({
                        'Name': '{server:9}| File-Based:     [DIR]  {ticket}'.format(server=server['Name'], ticket=d.name),
                        'Server': server,
                        'Source': d})

    # Check for images and subfolders
    for ticket_folder in sources.copy():
        for item in os.scandir(ticket_folder['Source'].path):
            if item.is_dir():
                # Add folder to sources
                sources.append({
                    'Name':                 '{server:9}| File-Based:     [DIR]  {ticket}\\{folder}'.format(
                        folder =            item.name,
                        server =            ticket_folder['Server']['Name'],
                        ticket =            ticket_folder['Source'].name),
                    'Server':               ticket_folder['Server'],
                    'Source':               item})

                # Check for images in folder
                for subitem in os.scandir(item.path):
                    if REGEX_WIM_FILE.search(item.name):
                        # Add image to sources
                        try:
                            size = human_readable_size(item.stat().st_size)
                        except:
                            size = '  ?  ?' # unknown
                        sources.append({
                            'Disabled':     bool(not is_valid_wim_image(subitem)),
                            'Name':         '{server:9}| Image-Based:  {size:>7}  {ticket}\\{folder}\\{image}'.format(
                                folder =    item.name,
                                image =     subitem.name,
                                server =    ticket_folder['Server']['Name'],
                                size =      size,
                                ticket =    ticket_folder['Source'].name),
                            'Server':       ticket_folder['Server'],
                            'Source':       subitem})
            elif REGEX_WIM_FILE.search(item.name):
                # Add image to sources
                try:
                    size = human_readable_size(item.stat().st_size)
                except:
                    size = '  ?  ?' # unknown
                sources.append({
                    'Disabled':             bool(not is_valid_wim_image(item)),
                    'Name':                 '{server:9}| Image-Based:  {size:>7}  {ticket}\\{image}'.format(
                        image =             item.name,
                        server =            ticket_folder['Server']['Name'],
                        size =              size,
                        ticket =            ticket_folder['Source'].name),
                    'Server':               ticket_folder['Server'],
                    'Source':               item})

    # Build Menu
    sources.sort(key=itemgetter('Name'))
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]

    # Select backup from sources
    if len(sources) > 0:
        selection = menu_select('Which backup are we using?', sources, actions, disabled_label='DAMAGED')
        if selection == 'Q':
            umount_backup_shares()
            exit_script()
        else:
            global_vars['Data']['Source'] = sources[int(selection)-1]['Source']
    else:
        print_error('ERROR: No backups found for ticket: {TicketNumber}.'.format(**global_vars))
        umount_backup_shares()
        pause("Press Enter to exit...")
        exit_script()

def select_destination():
    """Select destination for data 1 transfer."""
    disk = select_disk()
    path = '{disk}{folder_path}_{Date}'.format(
        disk =          disk['Disk'].mountpoint,
        folder_path =   'WK\\Transfer' if 'fixed' in disk['Disk'].opts else 'WK-Transfer',
        **global_vars)

    # Avoid merging with existing transfer
    path = non_clobber_rename(path)
    os.makedirs(path, exist_ok=True)

    global_vars['Data']['Destination'] = path

def select_disk():
    """Select disk from attached disks. returns dict."""
    actions =   [{'Name': 'Quit', 'Letter': 'Q'}]
    disks =     []
    for d in psutil.disk_partitions():
        info = {
            'Disk': d,
            'Name': d.mountpoint}
        try:
            usage = psutil.disk_usage(d.device)
            free = '{free} / {total} available'.format(
                free = human_readable_size(usage.free, 2),
                total = human_readable_size(usage.total, 2))
        except:
            # Meh, leaving unsupported destinations out
            pass
            # free = 'Unknown'
            # info['Disabled'] = True
        else:
            info['Display Name'] = '{disk}  ({free})'.format(disk=info['Name'], free=free)
            disks.append(info)

    selection = menu_select('Which disk are we transferring to?', disks, actions)
    if selection == 'Q':
        exit_script()
    else:
        return disks[int(selection)-1]

def transfer_backup():
    if 'Source' not in global_vars['Data']:
        raise Exception
    backup = global_vars['Data']['Source']

    if backup.is_dir():
        # File-Based
        transfer_backup_file_based()
    else:
        # Image-Based
        if REGEX_WIM_FILE.search(backup.name):
            transfer_backup_image_based()
        else:
            print_error('ERROR: Unsupported image: {}'.format(backup.path))
            raise GenericError

def transfer_backup_file_based():
    if 'Source' not in global_vars['Data'] or 'Selected Items' not in global_vars['Data']:
        raise Exception
    backup =            global_vars['Data']['Source']
    selected_items =    global_vars['Data']['Selected Items']

    # Run FastCopy for each selection "group"
    for group in selected_items:
        try_and_print(message=group['Message'], function=run_fast_copy, cs='Done', items=group['Items'], dest=group['Destination'])

def transfer_backup_image_based():
    if 'Source' not in global_vars['Data'] or 'Selected Items' not in global_vars['Data']:
        raise Exception
    backup =            global_vars['Data']['Source']
    selected_items =    global_vars['Data']['Selected Items']

    # Run wimlib-imagex for each selection "group"
    for group in selected_items:
        try_and_print(message=group['Message'], function=run_wimextract, cs='Done', source=global_vars['Data']['Source'].path, items=group['Items'], dest=group['Destination'])

def umount_backup_shares():
    """Unnount the backup shares regardless of current status."""
    for server in BACKUP_SERVERS:
        try:
            # Umount
            run_program('net use \\\\{IP}\\{Share} /delete'.format(**server))
            print_info('Umounted {Name}'.format(**server))
            server['Mounted'] = False
        except:
            print_error('Failed to umount \\\\{Name}\\{Share}.'.format(**server))
            sleep(1)

def wim_contains(source_path=None, file_path=None):
    if file_path is None or source_path is None:
        raise Exception

    _cmd = [
        global_vars['Tools']['wimlib-imagex'], 'dir',
        '{source}'.format(source=source_path), '1',
        '--path={}'.format(file_path),
        '--one-file-only']
    try:
        run_program(_cmd)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

# Kit Updates
def download_file(out_dir, out_name, source_url):
    """Downloads a file using curl."""
    extract_item('curl', silent=True)
    _cmd = [
        global_vars['Tools']['curl'],
        # '-#LSfo', # ProgressBar
        '-Lfso',
        '{out_dir}/{out_name}'.format(out_dir=out_dir, out_name=out_name),
        source_url]
    os.makedirs(out_dir, exist_ok=True)
    run_program(_cmd, pipe=False)

def resolve_dynamic_url(source_url, regex):
    """Download the "download page" and scan for a url using the regex provided; returns str."""
    # Download the "download page"
    extract_item('curl', silent=True)
    _tmp_file = '{TmpDir}/webpage.tmp'.format(**global_vars)
    _cmd = [
        global_vars['Tools']['curl'],
        '-#LSfo',
        _tmp_file,
        source_url]
    try:
        run_program(_cmd)
    except:
        # "Fail silently as the download_file() function will catch it
        return None

    # Scan the file for the regex
    with open(_tmp_file, 'r') as file:
        for line in file:
            if re.search(regex, line):
                _url = line.strip()
                _url = re.sub(r'.*(a |)href="([^"]+)".*', r'\2', _url)
                _url = re.sub(r".*(a |)href='([^']+)'.*", r'\2', _url)
                break

    # Cleanup and return
    os.remove(_tmp_file)
    return _url

def update_adwcleaner():
    _path = global_vars['BinDir']
    _name = 'AdwCleaner.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/adwcleaner/dl/125/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/a/adwcleaner/AdwCleaner\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_eset():
    _path = global_vars['BinDir']
    _name = 'ESET.exe'
    _url = 'http://download.eset.com/special/eos/esetsmartinstaller_enu.exe'
    download_file(_path, _name, _url)

def update_jrt():
    _path = global_vars['BinDir']
    _name = 'JRT.exe'
    _url = 'http://downloads.malwarebytes.org/file/jrt'
    download_file(_path, _name, _url)

def update_kvrt():
    _path = global_vars['BinDir']
    _name = 'KVRT.exe'
    _url = 'http://devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe'
    download_file(_path, _name, _url)

def update_hitmanpro():
    _path = '{BinDir}/HitmanPro'.format(**global_vars)
    _name = 'HitmanPro.exe'
    _url = 'http://dl.surfright.nl/HitmanPro.exe'
    download_file(_path, _name, _url)

    _name = 'HitmanPro64.exe'
    _url = 'http://dl.surfright.nl/HitmanPro_x64.exe'
    download_file(_path, _name, _url)

def update_intel_driver_utility():
    _path = '{BinDir}/_Drivers'.format(**global_vars)
    _name = 'Intel Driver Update Utility.exe'
    _dl_page = 'http://www.intel.com/content/www/us/en/support/detect.html'
    _regex = r'a href.*http(s|)://downloadmirror\.intel\.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+/Intel%20Driver%20Update%20Utility%20Installer.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_intel_ssd_toolbox():
    _path = '{BinDir}/_Drivers'.format(**global_vars)
    _name = 'Intel SSD Toolbox.exe'
    _dl_page = 'https://downloadcenter.intel.com/download/26085/Intel-Solid-State-Drive-Toolbox'
    _regex = r'href=./downloads/eula/[0-9]+/Intel-Solid-State-Drive-Toolbox.httpDown=https\%3A\%2F\%2Fdownloadmirror\.intel\.com\%2F[0-9]+\%2Feng\%2FIntel\%20SSD\%20Toolbox\%20-\%20v[0-9\.]+.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    _url = re.sub(r'.*httpDown=(.*)', r'\1', _url, flags=re.IGNORECASE)
    _url = _url.replace('%3A', ':')
    _url = _url.replace('%2F', '/')
    download_file(_path, _name, _url)

def update_rkill():
    _path = '{BinDir}/RKill'.format(**global_vars)
    _name = 'RKill.exe'
    _dl_page = 'http://www.bleepingcomputer.com/download/rkill/dl/10/'
    _regex = r'href=.*http(s|)://download\.bleepingcomputer\.com/dl/[a-zA-Z0-9]+/[a-zA-Z0-9]+/windows/security/security-utilities/r/rkill/rkill\.exe'
    _url = resolve_dynamic_url(_dl_page, _regex)
    download_file(_path, _name, _url)

def update_samsung_magician():
    print_warning('Disabled.')
    #~Broken~# _path = '{BinDir}/_Drivers'.format(**global_vars)
    #~Broken~# _name = 'Samsung Magician.zip'
    #~Broken~# _dl_page = 'http://www.samsung.com/semiconductor/minisite/ssd/download/tools.html'
    #~Broken~# _regex = r'href=./semiconductor/minisite/ssd/downloads/software/Samsung_Magician_Setup_v[0-9]+.zip'
    #~Broken~# _url = resolve_dynamic_url(_dl_page, _regex)
    #~Broken~# # Convert relative url to absolute
    #~Broken~# _url = 'http://www.samsung.com' + _url
    #~Broken~# download_file(_path, _name, _url)
    #~Broken~# # Extract and replace old copy
    #~Broken~# _args = [
    #~Broken~#     'e', '"{BinDir}/_Drivers/Samsung Magician.zip"'.format(**global_vars),
    #~Broken~#     '-aoa', '-bso0', '-bsp0',
    #~Broken~#     '-o"{BinDir}/_Drivers"'.format(**global_vars)
    #~Broken~# ]
    #~Broken~# run_program(seven_zip, _args)
    #~Broken~# try:
    #~Broken~#     os.remove('{BinDir}/_Drivers/Samsung Magician.zip'.format(**global_vars))
    #~Broken~#     #~PoSH~# Move-Item "$bin\_Drivers\Samsung*exe" "$bin\_Drivers\Samsung Magician.exe" $path 2>&1 | Out-Null
    #~Broken~# except:
    #~Broken~#     pass
    pass

def update_sysinternalssuite():
    _path = '{BinDir}/tmp'.format(**global_vars)
    _name = 'SysinternalsSuite.zip'
    _url = 'https://download.sysinternals.com/files/SysinternalsSuite.zip'
    download_file(_path, _name, _url)
    # Extract
    _args = [
        'e', '"{BinDir}/tmp/SysinternalsSuite.zip"'.format(**global_vars),
        '-aoa', '-bso0', '-bsp0',
        '-o"{BinDir}/SysinternalsSuite"'.format(**global_vars)]
    run_program(seven_zip, _args)
    try:
        os.remove('{BinDir}/tmp/SysinternalsSuite.zip'.format(**global_vars))
    except:
        pass

def update_tdsskiller():
    _path = global_vars['BinDir']
    _name = 'TDSSKiller.exe'
    _url = 'http://media.kaspersky.com/utilities/VirusUtilities/EN/tdsskiller.exe'
    download_file(_path, _name, _url)

# Installations
def install_adobe_reader():
    cmd = [
        '{BaseDir}/Installers/Extras/Office/Adobe Reader DC.exe'.format(**global_vars),
        '/sAll',
        '/msi', '/norestart', '/quiet',
        'ALLUSERS=1',
        'EULA_ACCEPT=YES']
    try_and_print(message='Adobe Reader DC...', function=run_program, cmd=cmd)

def install_chrome_extensions():
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Google\Chrome\Extensions', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY)
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY)
    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Google\Chrome\Extensions\cjpalhdlnbpafiamejdnhcphjbkeiagm', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY) as _key:
        winreg.SetValueEx(_key, 'update_url', 0, winreg.REG_SZ, 'https://clients2.google.com/service/update2/crx')
    winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY)
    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r'Software\Google\Chrome\Extensions\pgdnlhfefecpicbbihgmbmffkjpaplco', 0, winreg.KEY_WRITE | winreg.KEY_WOW64_32KEY) as _key:
        winreg.SetValueEx(_key, 'update_url', 0, winreg.REG_SZ, 'https://clients2.google.com/service/update2/crx')

def install_classicstart_skin():
    if global_vars['OS']['Version'] not in ['8', '10']:
        raise UnsupportedOSError
    extract_item('ClassicStartSkin', silent=True)
    _source = '{BinDir}\\ClassicStartSkin\\Metro-Win10-Black.skin7'.format(**global_vars)
    _dest_path = '{PROGRAMFILES}\\Classic Shell\\Skins'.format(**global_vars['Env'])
    _dest = '{dest_path}\\Metro-Win10-Black.skin7'.format(dest_path=_dest_path)
    os.makedirs(_dest_path, exist_ok=True)
    shutil.copy(_source, _dest)

def install_firefox_extensions():
    extract_item('FirefoxExtensions', silent=True)
    extensions = ['uBlock0@raymondhill.net']
    dests = ['{PROGRAMFILES}\\Mozilla Firefox\\distribution\\extensions'.format(**global_vars['Env'])]
    if 'PROGRAMFILES(X86)' in global_vars['Env']:
        dests.append('{PROGRAMFILES(X86)}\\Mozilla Firefox\\distribution\\extensions'.format(**global_vars['Env']))
    for extension in extensions:
        _source = '{BinDir}\\FirefoxExtensions\\{extension}'.format(extension=extension, **global_vars)
        for dest in dests:
            _dest = '{}\\{}'.format(dest, extension)
            if not os.path.exists(dest):
                shutil.copytree(_source, _dest)

def install_ninite_bundle(mse=False):
    if global_vars['OS']['Version'] in ['8', '10']:
        # Modern selection
        popen_program('{BaseDir}/Installers/Extras/Bundles/Modern.exe'.format(**global_vars))
    else:
        # Legacy selection
        if mse:
            popen_program('{BaseDir}/Installers/Extras/Security/Microsoft Security Essentials.exe'.format(**global_vars))
        popen_program('{BaseDir}/Installers/Extras/Bundles/Legacy.exe'.format(**global_vars))

def install_vcredists():
    extract_item('_vcredists', silent=True)
    prev_dir = os.getcwd()
    os.chdir('{BinDir}/_vcredists'.format(**global_vars))
    for vcr in VCR_REDISTS:
        try_and_print(message=vcr['Name'], function=run_program, cmd=vcr['Cmd'])

    os.chdir(prev_dir)

# Network
def check_connection():
    while True:
        result = try_and_print(message='Ping test...',  function=ping_test, cs='OK')
        if result['CS']:
            break
        else:
            if not ask('ERROR: System appears offline, try again?'):
                abort()

def ping_test(addr='google.com'):
    """Attempt to ping addr and if unsuccessful either retry or abort."""
    _cmd = ['ping', '-n', '2', addr]
    run_program(_cmd)

# OSR / VR
def run_autoruns():
    """Run AutoRuns in the background with VirusTotal checks enabled."""
    extract_item('SysinternalsSuite', filter='autoruns*', silent=True)
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'checkvirustotal', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'shownomicrosoft', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'shownowindows', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'showonlyvirustotal', 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(_key, 'submitvirustotal', 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(_key, 'verifysignatures', 0, winreg.REG_DWORD, 1)
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\SigCheck')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\SigCheck', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\Streams')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\Streams', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\VirusTotal')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\AutoRuns\VirusTotal', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'VirusTotalTermsAccepted', 0, winreg.REG_DWORD, 1)
    popen_program(global_vars['Tools']['AutoRuns'], minimized=True)

def run_chkdsk():
    """Run CHKDSK in a "split window" and report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        _cmd = [
            'chkdsk',
            '{SYSTEMDRIVE}'.format(**global_vars['Env']),
            '/scan', '/perf']
    else:
        _cmd = [
            'chkdsk',
            '{SYSTEMDRIVE}'.format(**global_vars['Env'])]
    _out = run_program(_cmd, check=False)
    # retcode == 0: no issues
    # retcode == 1: fixed issues (also happens when chkdsk.exe is killed?)
    # retcode == 2: issues
    if int(_out.returncode) > 0:
        # print_error('  ERROR: CHKDSK encountered errors')
        raise GenericError

    # Save stderr
    with open('{LogDir}\\CHKDSK.err'.format(**global_vars), 'a') as f:
        for line in _out.stderr.decode().splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open('{LogDir}\\CHKDSK.log'.format(**global_vars), 'a') as f:
        for line in _out.stdout.decode().splitlines():
            f.write(line.strip() + '\n')

def run_chkdsk_offline():
    """Set filesystem 'dirty bit' to force a chkdsk during next boot."""
    _cmd = [
        'fsutil', 'dirty', 'set',
        '{SYSTEMDRIVE}'.format(**global_vars['Env'])]
    _out = run_program(_cmd, check=False)
    if int(_out.returncode) > 0:
        raise GenericError

def run_chkdsk_spotfix():
    """Run CHKDSK in a "split window" and report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        _cmd = [
            'chkdsk',
            '{SYSTEMDRIVE}'.format(**global_vars['Env']),
            '/scan', '/perf']
    else:
        raise UnsupportedOSError
    _out = run_program(_cmd, check=False)
    # retcode == 0: no issues
    # retcode == 1: fixed issues (also happens when chkdsk.exe is killed?)
    # retcode == 2: issues
    if int(_out.returncode) > 0:
        # print_error('  ERROR: CHKDSK encountered errors')
        raise GenericError

    # Save stderr
    with open('{LogDir}\\CHKDSK_Spotfix.err'.format(**global_vars), 'a') as f:
        for line in _out.stderr.decode().splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open('{LogDir}\\CHKDSK_Spotfix.log'.format(**global_vars), 'a') as f:
        for line in _out.stdout.decode().splitlines():
            f.write(line.strip() + '\n')

def run_dism_restore_health():
    """Run DISM /ScanHealth, then /CheckHealth, and then report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        # Scan Health
        _cmd = [
            'DISM', '/Online', '/Cleanup-Image', '/RestoreHealth',
            '/LogPath:"{LogDir}\\DISM_RestoreHealth.log"'.format(**global_vars),
            '-new_console:n', '-new_console:s33V']
        run_program(_cmd, pipe=False, check=False, shell=True)
        wait_for_process('dism')
        # Now check health
        _cmd = [
            'DISM', '/Online', '/Cleanup-Image', '/CheckHealth',
            '/LogPath:"{LogDir}\\DISM_CheckHealth.log"'.format(**global_vars)]
        _result = run_program(_cmd, shell=True).stdout.decode()
        # Check result
        if re.search(r'No component store corruption detected', _result, re.IGNORECASE):
            pass
        else:
            raise GenericError
    else:
        raise UnsupportedOSError

def run_dism_scan_health():
    """Run DISM /ScanHealth, then /CheckHealth, and then report errors."""
    if global_vars['OS']['Version'] in ['8', '10']:
        # Scan Health
        _cmd = [
            'DISM', '/Online', '/Cleanup-Image', '/ScanHealth',
            '/LogPath:"{LogDir}\\DISM_ScanHealth.log"'.format(**global_vars),
            '-new_console:n', '-new_console:s33V']
        run_program(_cmd, pipe=False, check=False, shell=True)
        wait_for_process('dism')
        # Now check health
        _cmd = [
            'DISM', '/Online', '/Cleanup-Image', '/CheckHealth',
            '/LogPath:"{LogDir}\\DISM_CheckHealth.log"'.format(**global_vars)]
        _result = run_program(_cmd, shell=True).stdout.decode()
        # Check result
        if re.search(r'No component store corruption detected', _result, re.IGNORECASE):
            pass
        else:
            raise GenericError
    else:
        raise UnsupportedOSError

def run_hitmanpro():
    """Run HitmanPro in the background."""
    extract_item('HitmanPro', silent=True)
    _cmd = [
        global_vars['Tools']['HitmanPro'],
        '/quiet', '/noinstall', '/noupload',
        '/log={LogDir}\\hitman.xml'.format(**global_vars)]
    popen_program(_cmd)

def run_kvrt():
    """Run KVRT."""
    extract_item('KVRT', silent=True)
    os.makedirs(global_vars['QuarantineDir'], exist_ok=True)
    _cmd = [
        global_vars['Tools']['KVRT'],
        '-accepteula', '-dontcryptsupportinfo', '-fixednames',
        '-d', global_vars['QuarantineDir'],
        '-processlevel', '3']
    popen_program(_cmd, pipe=False)

def run_process_killer():
    """Kill most running processes skipping those in the whitelist.txt."""
    # borrowed from TronScript (reddit.com/r/TronScript) and credit to /u/cuddlychops06
    _prev_dir = os.getcwd()
    extract_item('ProcessKiller', silent=True)
    os.chdir('{BinDir}\\ProcessKiller'.format(**global_vars))
    run_program(['ProcessKiller.exe', '/silent'], check=False)
    os.chdir(_prev_dir)

def run_rkill():
    """Run RKill and cleanup afterwards."""
    extract_item('RKill', silent=True)
    _cmd = [
        global_vars['Tools']['RKill'],
        '-l', '{LogDir}\\RKill.log'.format(**global_vars),
        '-new_console:n', '-new_console:s33V']
    run_program(_cmd, check=False)
    wait_for_process('RKill')
    kill_process('notepad.exe')

    # RKill cleanup
    if os.path.exists('{USERPROFILE}\\Desktop'.format(**global_vars['Env'])):
        for item in os.scandir('{USERPROFILE}\\Desktop'.format(**global_vars['Env'])):
            if re.search(r'^RKill', item.name, re.IGNORECASE):
                _name = re.sub(r'^(.*)\.', '\1_{Date-Time}'.format(**global_vars), item.name, re.IGNORECASE)
                _name = '{ClientDir}\\Info\\{name}'.format(name=_name, **global_vars)
                shutil.move(item.path, non_clobber_rename(_name))

def run_sfc_scan():
    """Run SFC in a "split window" and report errors."""
    _cmd = [
        '{SYSTEMROOT}\\System32\\sfc.exe'.format(**global_vars['Env']),
        '/scannow']
    _out = run_program(_cmd, check=False)
    # Save stderr
    with open('{LogDir}\\SFC.err'.format(**global_vars), 'a') as f:
        for line in _out.stderr.decode('utf-8', 'ignore').splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open('{LogDir}\\SFC.log'.format(**global_vars), 'a') as f:
        for line in _out.stdout.decode('utf-8', 'ignore').splitlines():
            f.write(line.strip() + '\n')
    # Check result
    log_text = _out.stdout.decode('utf-8', 'ignore').replace('\0', '')
    if re.findall(r'did\s+not\s+find\s+any\s+integrity\s+violations', log_text):
        pass
    elif re.findall(r'successfully\s+repaired\s+them', log_text):
        raise GenericRepair
    else:
        raise GenericError

def run_tdsskiller():
    """Run TDSSKiller."""
    extract_item('TDSSKiller', silent=True)
    os.makedirs('{QuarantineDir}\\TDSSKiller'.format(**global_vars), exist_ok=True)
    _cmd = [
        global_vars['Tools']['TDSSKiller'],
        '-l', '{LogDir}\\TDSSKiller.log'.format(**global_vars),
        '-qpath', '{QuarantineDir}\\TDSSKiller'.format(**global_vars),
        '-accepteula', '-accepteulaksn',
        '-dcexact', '-tdlfs']
    run_program(_cmd, pipe=False)

# Windows Activation
def activate_windows_with_bios():
    """Attempt to activate Windows with a key stored in the BIOS."""
    # Code borrowed from https://github.com/aeruder/get_win8key
    #####################################################
    #script to query windows 8.x OEM key from PC firmware
    #ACPI -> table MSDM -> raw content -> byte offset 56 to end
    #ck, 03-Jan-2014 (christian@korneck.de)
    #####################################################
    bios_key = None
    table = b"MSDM"
    if acpi.FindAcpiTable(table) is True:
        rawtable = acpi.GetAcpiTable(table)
        #http://msdn.microsoft.com/library/windows/hardware/hh673514
        #byte offset 36 from beginning = Microsoft 'software licensing data structure' / 36 + 20 bytes offset from beginning = Win Key
        bios_key = rawtable[56:len(rawtable)].decode("utf-8")
    else:
        raise Exception('ACPI table {} not found.'.format(str(table)))
    if bios_key is None:
        raise BIOSKeyNotFoundError

    # Install Key
    run_program('cscript {SYSTEMROOT}\\System32\\slmgr.vbs /ipk {pkey} //nologo'.format(**global_vars['Env'], pkey=bios_key), check=False)
    sleep(5)

    # Attempt activation
    run_program('cscript {SYSTEMROOT}\\System32\\slmgr.vbs /ato //nologo'.format(**global_vars['Env']), check=False)
    sleep(5)

    # Check status
    if not windows_is_activated():
        raise Exception('Activation Failed')

def update_windows_activation_status():
    if not re.search(r'(permanent|safe mode)', global_vars['OS']['Activation'], re.IGNORECASE):
        _out = run_program('cscript /nologo {SYSTEMROOT}\\System32\\slmgr.vbs /xpr'.format(**global_vars['Env']))
        _out = _out.stdout.decode().splitlines()
        _out = [l for l in _out if re.match(r'^\s', l)]
        if len(_out) > 0:
            global_vars['OS']['Activation'] = re.sub(r'^\s+', '', _out[0])
        else:
            global_vars['OS']['Activation'] = 'Activation status unknown'

def windows_is_activated():
    """Updates activation status, checks if activated, and returns a bool."""
    update_windows_activation_status()
    return re.search(r'permanent', global_vars['OS']['Activation'], re.IGNORECASE)

# System Info
def backup_file_list():
    """Export current file listing for the system."""
    extract_item('Everything', silent=True)
    _cmd = [
        global_vars['Tools']['Everything'],
        '-nodb',
        '-create-filelist',
        '{LogDir}\\File List.txt'.format(**global_vars),
        '{SYSTEMDRIVE}'.format(**global_vars['Env'])]
    run_program(_cmd)

def backup_power_plans():
    """Export current power plans."""
    os.makedirs('{BackupDir}\\Power Plans'.format(**global_vars), exist_ok=True)
    _plans = run_program('powercfg /L')
    _plans = _plans.stdout.decode().splitlines()
    _plans = [p for p in _plans if re.search(r'^Power Scheme', p)]
    for p in _plans:
        _guid = re.sub(r'Power Scheme GUID:\s+([0-9a-f\-]+).*', r'\1', p)
        _name = re.sub(r'Power Scheme GUID:\s+[0-9a-f\-]+\s+\(([^\)]+)\).*', r'\1', p)
        # print('  {name} ({guid})'.format(guid=_guid, name=_name))
        _out = '{BackupDir}\\Power Plans\\{name}.pow'.format(name=_name, **global_vars)
        if not os.path.exists(_out):
            _cmd = ['powercfg', '-export', _out, _guid]
            run_program(_cmd, check=False)

def backup_registry():
    extract_item('erunt', silent=True)
    _args = [
        '{LogDir}\\Registry'.format(**global_vars),
        'sysreg',
        'curuser',
        'otherusers',
        '/noprogresswindow']
    run_program(global_vars['Tools']['ERUNT'], _args)

def compress_info():
    path = '{ClientDir}'.format(**global_vars)
    file = 'Info_{Date-Time}.7z'.format(**global_vars)
    _cmd = [
        global_vars['Tools']['SevenZip'],
        'a', '-t7z', '-mx=9', '-bso0', '-bse0',
        '{path}\\{file}'.format(path=path, file=file),
        '{ClientDir}\\Info'.format(**global_vars)]
    run_program(_cmd)

def find_software_hives():
    """Search for transferred SW hives and return a list."""
    hives = []
    search_paths = [global_vars['ClientDir']]

    while len(search_paths) > 0:
        for item in os.scandir(search_paths.pop(0)):
            if item.is_dir() and REGEX_REGISTRY_DIRS.search(item.name):
                search_paths.append(item.path)
            if item.is_file() and REGEX_SOFTWARE_HIVE.search(item.name):
                hives.append(item.path)

    return hives

def get_installed_office():
    programs = []
    with open ('{LogDir}\\Installed Program List (AIDA64).txt'.format(**global_vars), 'r') as f:
        for line in sorted(f.readlines()):
            if REGEX_OFFICE.search(line):
                programs.append(line[4:82].strip())

    if len(programs) == 0:
        programs = ['No programs found']
    return programs

def get_product_keys():
    keys = []

    with open ('{LogDir}\\Product Keys (ProduKey).txt'.format(**global_vars), 'r') as f:
        for line in f.readlines():
            if re.search(r'^Product Name', line):
                line = re.sub(r'^Product Name\s+:\s+(.*)', r'\1', line.strip())
                keys.append(line)

    if len(keys) == 0:
        keys = ['No product keys found']
    return keys

def get_user_data_size_info(all_users=True, indent=8, width=32):
    """Get size of user folders for all users and return a dict of dicts."""
    users = {}
    TMP_HIVE_PATH = 'HKU\\wk_tmp'
    # Extract and configure du
    extract_item('SysinternalsSuite', filter='du*', silent=True)
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\Du')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\Du', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)

    try:
        # Get SIDs
        if all_users:
            out = run_program('wmic useraccount get sid')
        else:
            out = run_program('wmic useraccount where name="{USERNAME}" get sid'.format(**global_vars['Env']))
        sids = out.stdout.decode().splitlines()
        sids = [s.strip() for s in sids if re.search(r'-1\d+$', s.strip())]

        # Get Usernames and add to _users
        for sid in sids:
            try:
                out = run_program('wmic useraccount where sid="{sid}" get name'.format(sid=sid))
                name = out.stdout.decode().splitlines()[2].strip()
                users[name] = {'Extra Folders': {}, 'Shell Folders': {}, 'SID': sid}
            except:
                # Just skip problem users
                pass
    except subprocess.CalledProcessError:
        # This results in an empty dict being returned, leaving it to the calling section to handle that case
        pass

    # Use username/SID pairs to check profile folder sizes
    for u in users.keys():
        try:
            # Main Profile path
            key = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{SID}'.format(**users[u])
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as _key:
                users[u]['ProfileImagePath'] = winreg.QueryValueEx(_key, 'ProfileImagePath')[0]
            try:
                out = run_program(global_vars['Tools']['Du'], ['-nobanner', '-q', users[u]['ProfileImagePath']])
                size = out.stdout.decode().splitlines()[4]
                size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                size = size.replace(',', '')
                size = human_readable_size(size)
                size_str = '{indent}{folder:<{width}}{size:>6} ({path})'.format(
                    indent =    ' ' * indent,
                    width =     width,
                    folder =    'Profile',
                    size =      size,
                    path =      users[u]['ProfileImagePath'])
                users[u]['ProfileSize'] = size_str
            except subprocess.CalledProcessError:
                # Failed to get folder size
                pass

            # Check if user hive is already loaded
            unload_hive = False
            try:
                # This tests if the user hive is already loaded and throws FileNotFoundError if not.
                winreg.QueryValue(winreg.HKEY_USERS, users[u]['SID'])
            except FileNotFoundError:
                # User not logged-in. Loading hive and setting unload_hive so it will be unloaded before the script exits.
                try:
                    _cmd = 'reg load {tmp_path} "{ProfileImagePath}\\NTUSER.DAT"'.format(tmp_path=TMP_HIVE_PATH, **users[u])
                    run_program(_cmd)
                    unload_hive = True
                except subprocess.CalledProcessError:
                    # Failed to load user hive
                    pass

            # Get Shell folder sizes
            key = r'{SID}\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'.format(**users[u])
            try:
                with winreg.OpenKey(winreg.HKEY_USERS, key) as _key:
                    for folder in SHELL_FOLDERS.keys():
                        for value in SHELL_FOLDERS[folder]:
                            try:
                                # Query value and break out of for look if successful
                                folder_path = winreg.QueryValueEx(_key, value)[0]
                                try:
                                    # Finally calculate folder size
                                    out = run_program(global_vars['Tools']['Du'], ['-nobanner', '-q', folder_path])
                                    size = out.stdout.decode().splitlines()[4]
                                    size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                                    size = size.replace(',', '')
                                    size = human_readable_size(size)
                                    str = '{indent}{folder:<{width}}{size:>6} ({path})'.format(
                                        indent =    ' ' * indent,
                                        width =     width,
                                        folder =    folder,
                                        size =      size,
                                        path =      folder_path)
                                    users[u]['Shell Folders'][folder] = str
                                except subprocess.CalledProcessError:
                                    # Failed to get folder size
                                    pass
                                break
                            except FileNotFoundError:
                                # Failed to query value above
                                pass
            except FileNotFoundError:
                # Can't read the user hive, skipping this user.
                pass

            # Extra shell folder check
            for folder in SHELL_FOLDERS.keys():
                if folder not in users[u]['Shell Folders']:
                    folder_path = '{ProfileImagePath}\\{folder}'.format(folder=folder, **users[u])
                    if os.path.exists(folder_path):
                        try:
                            out = run_program(global_vars['Tools']['Du'], ['-nobanner', '-q', folder_path])
                            size = out.stdout.decode().splitlines()[4]
                            size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                            size = size.replace(',', '')
                            size = human_readable_size(size)
                            str = '{indent}{folder:<{width}}{size:>6} ({path})'.format(
                                indent =    ' ' * indent,
                                width =     width,
                                folder =    folder,
                                size =      size,
                                path =      folder_path)
                            users[u]['Shell Folders'][folder] = str
                        except subprocess.CalledProcessError:
                            # Failed to get folder size
                            pass

            # Extra folder sizes
            for folder in EXTRA_FOLDERS:
                folder_path = '{ProfileImagePath}\\{folder}'.format(folder=folder, **users[u])
                if os.path.exists(folder_path):
                    try:
                        out = run_program(global_vars['Tools']['Du'], ['-nobanner', '-q', folder_path])
                        size = size.stdout.decode().splitlines()[4]
                        size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                        size = size.replace(',', '')
                        size = human_readable_size(size)
                        str = '{indent}{folder:<{width}}{size:>6} ({path})'.format(
                            indent =    ' ' * indent,
                            width =     width,
                            folder =    folder,
                            size =      size,
                            path =      folder_path)
                        users[u]['Extra Folders'][folder] = str
                    except subprocess.CalledProcessError:
                        # Failed to get folder size
                        pass
            # Unload user hive (if necessary)
            if unload_hive:
                _cmd = 'reg unload {tmp_path}'.format(tmp_path=TMP_HIVE_PATH)
                run_program(_cmd, check=False)

        except FileNotFoundError:
            # Can't find the ProfileImagePath, skipping this user.
            pass
        except:
            # Unload the wk_tmp hive no matter what
            _cmd = 'reg unload {tmp_path}'.format(tmp_path=TMP_HIVE_PATH)
            run_program(_cmd, check=False)
    # Done
    return users

def run_aida64():
    extract_item('AIDA64', silent=True)
    # All system info
    if not os.path.exists('{LogDir}\\System Information (AIDA64).html'.format(**global_vars)):
        _cmd = [
            global_vars['Tools']['AIDA64'],
            '/R', '{LogDir}\\System Information (AIDA64).html'.format(**global_vars),
            '/CUSTOM', '{BinDir}\\AIDA64\\full.rpf'.format(**global_vars),
            '/HTML', '/SILENT', '/SAFEST']
        run_program(_cmd, check=False)

    # Installed Programs
    if not os.path.exists('{LogDir}\\Installed Program List (AIDA64).txt'.format(**global_vars)):
        _cmd = [
            global_vars['Tools']['AIDA64'],
            '/R', '{LogDir}\\Installed Program List (AIDA64).txt'.format(**global_vars),
            '/CUSTOM', '{BinDir}\\AIDA64\\installed_programs.rpf'.format(**global_vars),
            '/TEXT', '/SILENT', '/SAFEST']
        run_program(_cmd, check=False)

    # Product Keys
    if not os.path.exists('{LogDir}\\Product Keys (AIDA64).txt'.format(**global_vars)):
        _cmd = [
            global_vars['Tools']['AIDA64'],
            '/R', '{LogDir}\\Product Keys (AIDA64).txt'.format(**global_vars),
            '/CUSTOM', '{BinDir}\\AIDA64\\licenses.rpf'.format(**global_vars),
            '/TEXT', '/SILENT', '/SAFEST']
        run_program(_cmd, check=False)

def run_bleachbit():
    if not os.path.exists('{LogDir}\\BleachBit.log'.format(**global_vars)):
        extract_item('BleachBit', silent=True)
        _cmd = [global_vars['Tools']['BleachBit'], '--preview', '--preset']
        _out = run_program(_cmd, check=False)
        # Save stderr
        if len(_out.stderr.decode().splitlines()) > 0:
            with open('{LogDir}\\BleachBit.err'.format(**global_vars), 'a') as f:
                for line in _out.stderr.decode().splitlines():
                    f.write(line.strip() + '\n')
        # Save stdout
        with open('{LogDir}\\BleachBit.log'.format(**global_vars), 'a') as f:
            for line in _out.stdout.decode().splitlines():
                f.write(line.strip() + '\n')

def run_hwinfo_sensors():
    _path = '{BinDir}\\HWiNFO'.format(**global_vars)
    for bit in [32, 64]:
        # Configure
        _source = '{path}\\general.ini'.format(path=_path)
        _dest =   '{path}\\HWiNFO{bit}.ini'.format(bit=bit, path=_path)
        shutil.copy(_source, _dest)
        with open(_dest, 'a') as f:
            f.write('SensorsOnly=1\n')
            f.write('SummaryOnly=0\n')
    popen_program(global_vars['Tools']['HWiNFO'])

def run_produkey():
    extract_item('ProduKey', silent=True)
    if not os.path.exists('{LogDir}\\Product Keys (ProduKey).txt'.format(**global_vars)):
        # Clear current configuration
        for config in ['ProduKey.cfg', 'ProduKey64.cfg']:
            try:
                if os.path.exists('{BinDir}\\ProduKey\\{config}'.format(config=config, **global_vars)):
                    os.remove('{BinDir}\\ProduKey\\{config}'.format(config=config, **global_vars))
            except:
                pass
        _cmd = [
            global_vars['Tools']['ProduKey'], '/nosavereg',
            '/stext', '{LogDir}\\Product Keys (ProduKey).txt'.format(**global_vars)]
        run_program(_cmd, check=False)

def run_xmplay():
    extract_item('XMPlay', silent=True)
    popen_program([global_vars['Tools']['XMPlay'], '{BinDir}\\XMPlay\\music.7z'.format(**global_vars)])

def show_disk_usage(disk=None):
    if disk is None:
        raise Exception
    print_standard(disk.device.replace('\\', ' '), end='', flush=True, timestamp=False)
    try:
        usage = psutil.disk_usage(disk.device)
        display_string = '{percent:>5.2f}% Free  ({free} / {total})'.format(
            percent = 100 - usage.percent,
            free = human_readable_size(usage.free, 2),
            total = human_readable_size(usage.total, 2))
        if usage.percent > 85:
            print_error(display_string, timestamp=False)
        elif usage.percent > 75:
            print_warning(display_string, timestamp=False)
        else:
            print_standard(display_string, timestamp=False)
    except:
        print_warning('Unknown', timestamp=False)

def show_free_space():
    """Show free space info for all fixed disks."""
    message = 'Free Space:'
    for disk in psutil.disk_partitions():
        try:
            if 'fixed' in disk.opts:
                try_and_print(disk=disk, message=message, function=show_disk_usage, ns='Unknown', silent_function=False)
                message = ''
        except:
            pass

def show_installed_ram():
    mem = psutil.virtual_memory()
    if mem.total > 5905580032:
        # > 5.5 Gb so 6Gb or greater
        print_standard(human_readable_size(mem.total).strip())
    elif mem.total > 3758096384:
        # > 3.5 Gb so 4Gb or greater
        print_warning(human_readable_size(mem.total).strip())
    else:
        print_error(human_readable_size(mem.total).strip())

def show_os_activation():
    act_str = global_vars['OS']['Activation']
    if re.search(r'permanent', act_str, re.IGNORECASE):
        print_standard(act_str, timestamp=False)
    elif re.search(r'unavailable', act_str, re.IGNORECASE):
        print_warning(act_str, timestamp=False)
    else:
        print_error(act_str, timestamp=False)

def show_os_name():
    os_name = global_vars['OS']['DisplayName']
    if global_vars['OS']['Arch'] == 32:
        # Show all 32-bit installs as an error message
        print_error(os_name, timestamp=False)
    else:
        if re.search(r'(unrecognized|very outdated)', os_name, re.IGNORECASE):
            print_error(os_name, timestamp=False)
        elif re.search(r'outdated', os_name, re.IGNORECASE):
            print_warning(os_name, timestamp=False)
        else:
            print_standard(os_name, timestamp=False)

def show_temp_files_size():
    # Temp file size
    size = None
    with open('{LogDir}\\BleachBit.log'.format(**global_vars), 'r') as f:
        for line in f.readlines():
            if re.search(r'^disk space to be recovered:', line, re.IGNORECASE):
                size = re.sub(r'.*: ', '', line.strip())
                size = re.sub(r'(\w)iB$', r' \1b', size)
    if size is None:
        print_warning(size, timestamp=False)
    else:
        print_standard(size, timestamp=False)

def show_user_data_summary(all_users=True, indent=8, width=32):
    users = get_user_data_size_info(all_users)
    for user in sorted(users.keys()):
        print_success('    User: {user}'.format(user=user))
        print_standard(users[user].get('ProfileSize', 'Unknown'))
        print_standard('{}{}'.format(' '*indent, '-'*(width+6)))
        for folder in sorted(users[user]['Shell Folders']):
            print_standard(users[user]['Shell Folders'][folder])
        for folder in sorted(users[user]['Extra Folders']):
            print_standard(users[user]['Shell Folders'][folder])

def upload_info():
    path = '{ClientDir}'.format(**global_vars)
    file = 'Info_{Date-Time}.7z'.format(**global_vars)
    upload_data(path, file)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
