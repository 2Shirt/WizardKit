# Wizard Kit: Software Diagnostics

import os
import re
import subprocess
import winreg

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Software Diagnostics Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['BackupDir'] = '{ClientDir}\\Backups\\{Date}'.format(**vars_wk)
vars_wk['LogFile'] = '{LogDir}\\Software Diagnostics.log'.format(**vars_wk)
vars_wk['AutoRuns'] = '{BinDir}\\SysinternalsSuite\\autoruns.exe'.format(**vars_wk)
vars_wk['BleachBit'] = '{BinDir}\\BleachBit\\bleachbit_console.exe'.format(**vars_wk)
vars_wk['ERUNT'] = '{BinDir}\\erunt\\ERUNT.EXE'.format(**vars_wk)
vars_wk['Everything'] = '{BinDir}\\Everything\\Everything.exe'.format(**vars_wk)
vars_wk['HitmanPro'] = '{BinDir}\\HitmanPro\\HitmanPro.exe'.format(**vars_wk)
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
vars_wk['ProduKey'] = '{BinDir}\\ProduKey\\ProduKey.exe'.format(**vars_wk)
vars_wk['SIV'] = '{BinDir}\\SIV\\SIV.exe'.format(**vars_wk)
vars_wk['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['AutoRuns'] = vars_wk['AutoRuns'].replace('.exe', '64.exe')
    vars_wk['Everything'] = vars_wk['Everything'].replace('.exe', '64.exe')
    vars_wk['HitmanPro'] = vars_wk['HitmanPro'].replace('.exe', '64.exe')
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('.exe', '64.exe')
    vars_wk['ProduKey'] = vars_wk['ProduKey'].replace('.exe', '64.exe')
    vars_wk['SIV'] = vars_wk['SIV'].replace('.exe', '64.exe')
    vars_wk['SevenZip'] = vars_wk['SevenZip'].replace('.exe', '64.exe')
os.makedirs(vars_wk['LogDir'], exist_ok=True)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    pause("Press Enter to exit...")
    exit_script()

def backup_browsers():
    print_info('* Backing up browser data', vars_wk['LogFile'])
    # Chromium
    if os.path.exists('{LOCALAPPDATA}\\Chromium'.format(**vars_wk['Env'])):
        print_standard('  Chromium', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Browsers\\{USERNAME}\\Chromium.7z" "{LOCALAPPDATA}\\Chromium"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    # Google Chrome
    if os.path.exists('{LOCALAPPDATA}\\Google\\Chrome'.format(**vars_wk['Env'])):
        print_standard('  Google Chrome', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Browsers\\{USERNAME}\\Google Chrome.7z" "{LOCALAPPDATA}\\Google\\Chrome"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    # Internet Explorer
    if os.path.exists('{USERPROFILE}\\Favorites'.format(**vars_wk['Env'])):
        print_standard('  Internet Explorer', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Browsers\\{USERNAME}\\Internet Explorer.7z" "{USERPROFILE}\\Favorites"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
        run_program('reg export "hkcu\\Software\\Microsoft\\Internet Explorer" "{BackupDir}\\Browsers\\{USERNAME}\\Internet Explorer (HKCU).reg" /y'.format(**vars_wk, **vars_wk['Env']), check=False)
        run_program('reg export "hklm\\Software\\Microsoft\\Internet Explorer" "{BackupDir}\\Browsers\\{USERNAME}\\Internet Explorer (HKLM).reg" /y'.format(**vars_wk, **vars_wk['Env']), check=False)
    # Mozilla Firefox
    if os.path.exists('{APPDATA}\\Mozilla\\Firefox'.format(**vars_wk['Env'])):
        print_standard('  Mozilla Firefox', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Browsers\\{USERNAME}\\Mozilla Firefox.7z" "{APPDATA}\\Mozilla\\Firefox\\Profile*"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)
    # Opera Chromium
    if os.path.exists('{APPDATA}\\Opera Software\\Opera Stable'.format(**vars_wk['Env'])):
        print_standard('  Opera Chromium', vars_wk['LogFile'])
        _cmd = '{SevenZip} a -aoa -bso0 -bse0 -mx=1 "{BackupDir}\\Browsers\\{USERNAME}\\Opera Chromium.7z" "{APPDATA}\\Mozilla\\Opera Software\\Opera Stable*"'.format(**vars_wk, **vars_wk['Env'])
        run_program(_cmd, check=False, pipe=False)

def backup_file_list():
    """Export current file listing for the system."""
    print_info('* Backing up file list', vars_wk['LogFile'])
    extract_item('Everything', vars_wk, silent=True)
    _cmd = [
        vars_wk['Everything'],
        '-nodb',
        '-create-filelist',
        '{LogDir}\\File List.txt'.format(**vars_wk),
        '{SYSTEMDRIVE}'.format(**vars_wk['Env'])]
    try:
        run_program(_cmd)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to save file list', vars_wk['LogFile'])

def backup_power_plans():
    """Export current power plans."""
    print_info('* Backing up power plans', vars_wk['LogFile'])
    os.makedirs('{BackupDir}\\Power Plans'.format(**vars_wk), exist_ok=True)
    try:
        _plans = run_program('powercfg /L')
        _plans = _plans.stdout.decode().splitlines()
        _plans = [p for p in _plans if re.search(r'^Power Scheme', p)]
        for p in _plans:
            _guid = re.sub(r'Power Scheme GUID:\s+([0-9a-f\-]+).*', r'\1', p)
            _name = re.sub(r'Power Scheme GUID:\s+[0-9a-f\-]+\s+\(([^\)]+)\).*', r'\1', p)
            print('  {name} ({guid})'.format(guid=_guid, name=_name))
            _out = '{BackupDir}\\Power Plans\\{name}.pow'.format(name=_name, **vars_wk)
            if not os.path.exists(_out):
                run_program('powercfg /export "{out}" {guid}'.format(out=_out, guid=_guid), check=False)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to export power plans.')

def backup_registry():
    print_info('* Backing up registry', vars_wk['LogFile'])
    extract_item('erunt', vars_wk, silent=True)
    _args = [
        '{LogDir}\\Registry'.format(**vars_wk),
        'sysreg',
        'curuser',
        'otherusers',
        '/noprogresswindow']
    try:
        run_program(vars_wk['ERUNT'], _args)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to backup registry', vars_wk['LogFile'])

def exit_script():
    quit()

def get_battery_info():
    #~#print_info('* Battery', vars_wk['LogFile'])
    #~#WK-write "==== Battery Check ====" "$log"
    #~#& "$wd\check_battery.ps1" "$log"
    #~#WK-write "" "$log"
    pass

def get_free_space():
    print_info('* Free space', vars_wk['LogFile'])
    for drive in get_free_space_info():
        print_standard('  {}  {}'.format(*drive))

def get_installed_office():
    print_info('* Installed Office programs', vars_wk['LogFile'])
    with open ('{LogDir}\\Installed Program List (SIV).txt'.format(**vars_wk), 'r', encoding='utf16') as f:
        for line in sorted(f.readlines()):
            if re.search(r'(Microsoft (Office\s+(365|Enterprise|Home|Pro(\s|fessional)|Single|Small|Standard|Starter|Ultimate|system)|Works[-\s\d]+\d)|(Libre|Open|Star)\s*Office|WordPerfect|Gnumeric|Abiword)', line, re.IGNORECASE):
                print_standard('  ' + line[18:96].strip(), vars_wk['LogFile'])

def get_installed_ram():
    print_info('* Installed RAM', vars_wk['LogFile'])
    with open ('{LogDir}\\RAM Information (SIV).txt'.format(**vars_wk), 'r', encoding='utf16') as f:
        for line in f.readlines():
            if re.search(r'^Memory', line, re.IGNORECASE):
                print_standard('  ' + line.strip(), vars_wk['LogFile'])

def get_os_info():
    print_info('* Operating System', vars_wk['LogFile'])
    if vars_wk['Arch'] == 32:
        # Show all 32-bit installs as an error message
        print_error('  {Name} x{Arch}'.format(**vars_wk), vars_wk['LogFile'])
    else:
        if vars_wk['CurrentVersion'] == '6.0':
            # Vista
            if vars_wk['CurrentBuildNumber'] < 6002:
                print_error('  {Name} x{Arch} (very outdated)'.format(**vars_wk), vars_wk['LogFile'])
            else:
                print_warning('  {Name} x{Arch}'.format(**vars_wk), vars_wk['LogFile'])
        elif vars_wk['CurrentVersion'] == '6.1':
            # Windows 7
            if vars_wk['CSDVersion'] == 'Service Pack 1':
                print_standard('  {Name} x{Arch}'.format(**vars_wk), vars_wk['LogFile'])
            else:
                print_error('  {Name} x{Arch} (very outdated)'.format(**vars_wk), vars_wk['LogFile'])
        elif vars_wk['CurrentVersion'] == '6.2':
            # Windows 8
            print_error('  {Name} x{Arch} (very outdated)'.format(**vars_wk), vars_wk['LogFile'])
        elif vars_wk['CurrentVersion'] == '6.3':
            if vars_wk['CurrentBuild'] == 9200:
                # Windows 8.1
                print_error('  {Name} x{Arch} (very outdated)'.format(**vars_wk), vars_wk['LogFile'])
            elif vars_wk['CurrentBuild'] == 9600:
                # Windows 8.1 Update
                print_info('  {Name} x{Arch}'.format(**vars_wk), vars_wk['LogFile'])
            elif vars_wk['CurrentBuild'] == 10240:
                # Windows 10 Threshold 1
                print_error('  {Name} x{Arch} (outdated)'.format(**vars_wk), vars_wk['LogFile'])
            elif vars_wk['CurrentBuild'] == 10586:
                # Windows 10 Threshold 2
                print_warning('  {Name} x{Arch} (outdated)'.format(**vars_wk), vars_wk['LogFile'])
            elif vars_wk['CurrentBuild'] == 14393:
                # Windows 10 Redstone 1
                print_standard('  {Name} x{Arch}'.format(**vars_wk), vars_wk['LogFile'])
            else:
                print_warning('  {Name} x{Arch} (unrecognized)'.format(**vars_wk), vars_wk['LogFile'])
    # OS Activation
    if re.search(r'permanent', vars_wk['Activation'], re.IGNORECASE):
        print_standard('  {Activation}'.format(**vars_wk))
    elif re.search(r'unavailable', vars_wk['Activation'], re.IGNORECASE):
        print_warning('  {Activation}'.format(**vars_wk))
    else:
        print_error('  {Activation}'.format(**vars_wk))

def get_product_keys():
    print_info('* Product Keys', vars_wk['LogFile'])
    # ProduKey
    with open ('{LogDir}\\Product Keys (ProduKey).txt'.format(**vars_wk), 'r') as f:
        _keys = []
        for line in f.readlines():
            if re.search(r'^Product Name', line):
                line = re.sub(r'^Product Name\s+:\s+(.*)', r'\1', line)
                _keys.append(line)
        for k in sorted(_keys):
            print_standard('  ' + k.strip(), vars_wk['LogFile'])

def get_ticket_number():
    """Get TicketNumber from user and save it in the info folder."""
    vars_wk['TicketNumber'] = None
    while vars_wk['TicketNumber'] is None:
        _ticket = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([-_]?\w+|))$', _ticket):
            vars_wk['TicketNumber'] = _ticket
            with open('{LogDir}\\TicketNumber'.format(**vars_wk), 'w') as f:
                f.write(_ticket)
        else:
            print_error('ERROR: Invalid ticket number', vars_wk['LogFile'])

def get_user_data_summary():
    print_info('* User Data', vars_wk['LogFile'])
    users = get_user_data_size_info(vars_wk)
    for user in sorted(users):
        print_standard('  User: {user}'.format(user=user), vars_wk['LogFile'])
        print_standard('    ' + users[user].get('ProfileSize', 'Unknown'), vars_wk['LogFile'])
        print_standard('    -------------------------------', vars_wk['LogFile'])
        for folder in sorted(users[user]['Shell Folders']):
            print_standard('    ' + users[user]['Shell Folders'][folder], vars_wk['LogFile'])
        for folder in sorted(users[user]['Extra Folders']):
            print_standard('    ' + users[user]['Shell Folders'][folder], vars_wk['LogFile'])

def ping_test(addr='google.com'):
    """Attempt to ping addr and if unsuccessful either retry or abort."""
    print_info('* Checking network connection', vars_wk['LogFile'])
    _cmd = ['ping', '-n', '2', addr]
    while True:
        try:
            run_program(_cmd)
            break
        except subprocess.CalledProcessError:
            if not ask('ERROR: Can\'t ping {addr}, try again?'.format(addr=addr), vars_wk['LogFile']):
                abort()

def run_process_killer():
    """Kill most running processes skipping those in the whitelist.txt."""
    # borrowed from TronScript (reddit.com/r/TronScript) and credit to /u/cuddlychops06
    print_info('* Stopping all processes', vars_wk['LogFile'])
    _prev_dir = os.getcwd()
    extract_item('ProcessKiller', vars_wk, silent=True)
    os.chdir('{BinDir}\\ProcessKiller'.format(**vars_wk))
    run_program(['ProcessKiller.exe', '/silent'], check=False)
    os.chdir(_prev_dir)

def run_autoruns():
    """Run AutoRuns in the background with VirusTotal checks enabled."""
    extract_item('SysinternalsSuite', vars_wk, filter='autoruns*', silent=True)
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
    # Set autoruns to start minimized
    info = subprocess.STARTUPINFO()
    info.dwFlags = subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 6
    subprocess.Popen(vars_wk['AutoRuns'], startupinfo=info)

def run_bleachbit():
    if not os.path.exists('{LogDir}\\BleachBit.log'.format(**vars_wk)):
        print_info('* Checking for temp files', vars_wk['LogFile'])
        extract_item('BleachBit', vars_wk, silent=True)
        _args = ['--preview', '--preset']
        _out = run_program(vars_wk['BleachBit'], _args, check=False)
        # Save stderr
        if len(_out.stderr.decode().splitlines()) > 0:
            with open('{LogDir}\\BleachBit.err'.format(**vars_wk), 'a') as f:
                for line in _out.stderr.decode().splitlines():
                    f.write(line.strip() + '\n')
        # Save stdout
        with open('{LogDir}\\BleachBit.log'.format(**vars_wk), 'a') as f:
            for line in _out.stdout.decode().splitlines():
                f.write(line.strip() + '\n')
        
    # Temp file size
    with open('{LogDir}\\BleachBit.log'.format(**vars_wk), 'r') as f:
        for line in f.readlines():
            if re.search(r'^(disk space.*recovered|files.*deleted)', line, re.IGNORECASE):
                print_standard('  ' + line.strip())

def run_chkdsk():
    """Run CHKDSK in a "split window" and report errors."""
    print_info('* Checking filesystem health', vars_wk['LogFile'])
    _cmd = [
        'chkdsk',
        '{SYSTEMDRIVE}'.format(**vars_wk['Env'])]
    _out = run_program(_cmd, check=False)
    if int(_out.returncode) > 1:
        # retcode == 0: no issues
        # retcode == 1: fixed issues
        # retcode == 2: issues
        print_error('  ERROR: CHKDSK encountered errors', vars_wk['LogFile'])
    
    # Save stderr
    with open('{LogDir}\\CHKDSK.err'.format(**vars_wk), 'a') as f:
        for line in _out.stderr.decode().splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open('{LogDir}\\CHKDSK.log'.format(**vars_wk), 'a') as f:
        for line in _out.stdout.decode().splitlines():
            f.write(line.strip() + '\n')

def run_dism_health_check():
    """Run DISM /ScanHealth, then /CheckHealth, and then report errors."""
    if vars_wk['Version'] in ['8', '10']:
        print_info('* Checking system image health', vars_wk['LogFile'])
        # Scan Health
        _args = [
            '/Online',
            '/Cleanup-Image',
            '/ScanHealth',
            '/LogPath:{LogDir}\\DISM_ScanHealth.log'.format(**vars_wk),
            '-new_console:n',
            '-new_console:s33V']
        run_program('dism', _args, pipe=False, check=False)
        wait_for_process('dism')
        # Now check health
        _args = [
            '/Online',
            '/Cleanup-Image',
            '/CheckHealth',
            '/LogPath:{LogDir}\\DISM_CheckHealth.log'.format(**vars_wk)]
        try:
            _result = run_program('dism', _args).stdout.decode()
        except subprocess.CalledProcessError:
            print_error('  ERROR: failed to run DISM health check', vars_wk['LogFile'])
            _result = ['Unknown']
        else:
            # Check result
            if not re.search(r'No component store corruption detected', _result, re.IGNORECASE):
                for line in _result:
                    line = '  ' + line
                    print_warning(line, vars_wk['LogFile'])
                print_error('  ERROR: DISM encountered errors, please review details above', vars_wk['LogFile'])

def run_hitmanpro():
    """Run HitmanPro in the background."""
    print_info('* Running malware/virus scan (in the background)', vars_wk['LogFile'])
    extract_item('HitmanPro', vars_wk, silent=True)
    _cmd = [
        vars_wk['HitmanPro'],
        '/quiet',
        '/noinstall',
        '/noupload',
        '/log={LogDir}\\hitman.xml'.format(**vars_wk)]
    subprocess.Popen(_cmd)

def run_produkey():
    extract_item('ProduKey', vars_wk, silent=True)
    if not os.path.exists('{LogDir}\\Product Keys (ProduKey).txt'.format(**vars_wk)):
        print_info('* Saving product keys (secondary method)', vars_wk['LogFile'])
        # Clear current configuration
        for config in ['ProduKey.cfg', 'ProduKey64.cfg']:
            try:
                if os.path.exists('{BinDir}\\ProduKey\\{config}'.format(config=config, **vars_wk)):
                    os.remove('{BinDir}\\ProduKey\\{config}'.format(config=config, **vars_wk))
            except:
                pass
        _args = ['/nosavereg', '/stext', '{LogDir}\\Product Keys (ProduKey).txt'.format(**vars_wk)]
        run_program(vars_wk['ProduKey'], _args, check=False)

def run_rkill():
    """Run RKill and cleanup afterwards."""
    print_info('* Running RKill', vars_wk['LogFile'])
    extract_item('RKill', vars_wk, silent=True)
    _cmd = [
        '{BinDir}\\RKill\\RKill.exe'.format(**vars_wk),
        '-l',
        '{LogDir}\\RKill.log'.format(**vars_wk),
        '-new_console:n',
        '-new_console:s33V']
    run_program(_cmd, check=False)
    wait_for_process('RKill')
    kill_process('notepad.exe')
    if not ask('  Did RKill run correctly?', vars_wk['LogFile']):
        print_warning('  Opening folder for manual execution.', vars_wk['LogFile'])
        try:
            subprocess.Popen(['explorer.exe', '{BinDir}\\RKill'.format(**vars_wk)])
        except:
            pass
        if not ask('  Resume script?'):
            abort()
    
    # RKill cleanup
    for item in os.scandir('{USERPROFILE}\\Desktop'.format(**vars_wk['Env'])):
        if re.search(r'^RKill', item.name, re.IGNORECASE):
            shutil.move(item.path, '{ClientDir}\\Info\\{name}'.format(name=item.name, **vars_wk))

def run_siv():
    extract_item('SIV', vars_wk, silent=True)
    # All system info
    if not os.path.exists('{LogDir}\\System Information (SIV).txt'.format(**vars_wk)):
        print_info('* Saving System information', vars_wk['LogFile'])
        _cmd = [
            vars_wk['SIV'],
            '-KEYS',
            '-LOCAL',
            '-UNICODE',
            '-SAVE={LogDir}\\System_Information_(SIV).txt'.format(**vars_wk)]
        run_program(_cmd, check=False)
    
    # RAM
    if not os.path.exists('{LogDir}\\RAM_Information_(SIV).txt'.format(**vars_wk)):
        _args = [
            '-KEYS',
            '-LOCAL',
            '-UNICODE',
            '-SAVE=[dimms]={LogDir}\\RAM_Information_(SIV).txt'.format(**vars_wk)]
        run_program(vars_wk['SIV'], _args, check=False)
    
    # Installed Programs
    if not os.path.exists('{LogDir}\\Installed Program List_(SIV).txt'.format(**vars_wk)):
        print_info('* Saving installed program list', vars_wk['LogFile'])
        _args = [
            '-KEYS',
            '-LOCAL',
            '-UNICODE',
            '-SAVE=[software]={LogDir}\\Installed_Program_List_(SIV).txt'.format(**vars_wk)]
        run_program(vars_wk['SIV'], _args, check=False)
    
    # Product Keys
    if not os.path.exists('{LogDir}\\Product Keys (SIV).txt'.format(**vars_wk)):
        print_info('* Saving product keys', vars_wk['LogFile'])
        _args = [
            '-KEYS',
            '-LOCAL',
            '-UNICODE',
            '-SAVE=[product-ids]={LogDir}\\Product_Keys_(SIV).txt'.format(**vars_wk)]
        run_program(vars_wk['SIV'], _args, check=False)
    extract_item('ProduKey', vars_wk, silent=True)
    
    # Rename files
    for item in os.scandir(vars_wk['LogDir']):
        if re.search(r'SIV', item.name, re.IGNORECASE):
            shutil.move(item.path, item.path.replace('_', ' ').title().replace('Siv', 'SIV'))

def run_sfc_scan():
    """Run SFC in a "split window" and report errors."""
    print_info('* Checking system file health', vars_wk['LogFile'])
    _cmd = [
        '{SYSTEMROOT}\\System32\\sfc.exe'.format(**vars_wk['Env']),
        '/scannow']
    _out = run_program(_cmd, check=False)
    # Save stderr
    with open('{LogDir}\\SFC.err'.format(**vars_wk), 'a') as f:
        for line in _out.stderr.decode().splitlines():
            f.write(line.strip() + '\n')
    # Save stdout
    with open('{LogDir}\\SFC.log'.format(**vars_wk), 'a') as f:
        for line in _out.stdout.decode().splitlines():
            f.write(line.strip() + '\n')

def run_tdsskiller():
    """Run TDSSKiller."""
    print_info('* Running rootkit scan', vars_wk['LogFile'])
    extract_item('TDSSKiller', vars_wk, silent=True)
    os.makedirs('{ClientDir}\\Quarantine\\TDSSKiller'.format(**vars_wk), exist_ok=True)
    _cmd = '{BinDir}\\TDSSKiller\\TDSSKiller.exe'.format(**vars_wk)
    _args = [
        '-l',
        '{LogDir}\\TDSSKiller.log'.format(**vars_wk),
        '-qpath',
        '{ClientDir}\\Quarantine\\TDSSKiller'.format(**vars_wk),
        '-accepteula',
        '-accepteulaksn',
        '-dcexact',
        '-tdlfs']
    try:
        run_program(_cmd, _args, pipe=False)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to run TDSSKiller.', vars_wk['LogFile'])
        abort()

def upload_info():
    print_info('* Uploading info to NAS', vars_wk['LogFile'])
    path = '{ClientDir}'.format(**vars_wk)
    file = 'Info_{Date-Time}.7z'.format(**vars_wk)
    
    # Compress Info
    _cmd = [
        vars_wk['SevenZip'],
        'a', '-t7z', '-mx=9', '-bso0', '-bse0',
        '{path}\\{file}'.format(path=path, file=file),
        '{ClientDir}\\Info'.format(**vars_wk)]
    try:
        run_program(_cmd, pipe=False)
    except subprocess.CalledProcessError:
        print_error('  ERROR: Failed to compress data for upload.', vars_wk['LogFile'])
        return
    
    # Upload Info
    try:
        upload_data(path, file, vars_wk)
    except:
        print_error('  ERROR: Failed to upload info.', vars_wk['LogFile'])

if __name__ == '__main__':
    stay_awake(vars_wk)
    get_ticket_number() 
    os.system('cls')
    print_info('Starting Software Diagnostics for Ticket #{TicketNumber}\n'.format(**vars_wk), vars_wk['LogFile'])
    
    # Sanitize Environment
    run_process_killer()
    run_rkill()
    run_tdsskiller()
    
    # Re-run if earlier process was stopped.
    stay_awake(vars_wk)
    
    # Network Check
    ping_test()
    
    # Start background scans
    run_hitmanpro()
    run_autoruns()
    
    # OS Health Checks
    run_chkdsk()
    run_sfc_scan()
    run_dism_health_check()
    
    # Export system info
    backup_file_list()
    backup_power_plans()
    backup_registry()
    backup_browsers()
    run_siv()
    run_produkey()
    
    # Summary
    run_bleachbit()
    get_free_space()
    get_installed_ram()
    get_installed_office()
    get_product_keys()
    get_os_info()
    get_battery_info()
    get_user_data_summary()
    
    # Upload info
    upload_info()
    
    # Done
    print_standard('\nDone.', vars_wk['LogFile'])
    pause('Press Enter to exit...')
    
    # Open log
    extract_item('Notepad2', vars_wk, silent=True)
    subprocess.Popen([vars_wk['Notepad2'], vars_wk['LogFile']])
    
    # Quit
    kill_process('caffeine.exe')
    exit_script()