# Wizard Kit: Software Diagnostics

import os
import re
import shutil
import subprocess
import winreg

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Software Checklist Tool')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['BackupDir'] = '{ClientDir}\\Backups\\{Date}'.format(**vars_wk)
vars_wk['LogFile'] = '{LogDir}\\Software Checklist.log'.format(**vars_wk)
vars_wk['AutoRuns'] = '{BinDir}\\SysinternalsSuite\\autoruns.exe'.format(**vars_wk)
vars_wk['ERUNT'] = '{BinDir}\\erunt\\ERUNT.EXE'.format(**vars_wk)
vars_wk['Everything'] = '{BinDir}\\Everything\\Everything.exe'.format(**vars_wk)
vars_wk['HWiNFO'] = '{BinDir}\\HWiNFO\\HWiNFO.exe'.format(**vars_wk)
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
vars_wk['ProduKey'] = '{BinDir}\\ProduKey\\ProduKey.exe'.format(**vars_wk)
vars_wk['SIV'] = '{BinDir}\\SIV\\SIV.exe'.format(**vars_wk)
vars_wk['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars_wk)
vars_wk['XMPlay'] = '{BinDir}\\XMPlay\\xmplay.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['AutoRuns'] = vars_wk['AutoRuns'].replace('.exe', '64.exe')
    vars_wk['Everything'] = vars_wk['Everything'].replace('.exe', '64.exe')
    vars_wk['HWiNFO'] = vars_wk['HWiNFO'].replace('.exe', '64.exe')
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('.exe', '64.exe')
    vars_wk['ProduKey'] = vars_wk['ProduKey'].replace('.exe', '64.exe')
    vars_wk['SIV'] = vars_wk['SIV'].replace('.exe', '64.exe')
    vars_wk['SevenZip'] = vars_wk['SevenZip'].replace('.exe', '64.exe')
os.makedirs(vars_wk['LogDir'], exist_ok=True)

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

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

def cleanup_adwcleaner():
    _path = '{SYSTEMDRIVE}\\AdwCleaner'.format(**vars_wk['Env'])
    if os.path.exists(_path):
        try:
            print_info('* Uninstalling AdwCleaner', vars_wk['LogFile'])
            os.makedirs('{ClientDir}\\Info'.format(**vars_wk), exist_ok=True)
            for entry in os.scandir(_path):
                if entry.is_file() and re.search(r'*.(log|txt)', entry.name):
                    shutil.move(entry.path, '{ClientDir}\\Info\\{name}'.format(name=entry.name, **vars_wk))
                elif entry.name == 'Quarantine':
                    os.makedirs('{ClientDir}\\Quarantine'.format(**vars_wk), exist_ok=True)
                    shutil.move(entry.path, '{ClientDir}\\Quarantine\\AdwCleaner'.format(**vars_wk))
            shutil.rmtree(_path)
        except:
            print_error('ERROR: Failed to uninstall AdwCleaner.', vars_wk['LogFile'])

def cleanup_desktop():
    print_info('* Checking Desktop for leftover files', vars_wk['LogFile'])
    os.makedirs('{ClientDir}\\Info'.format(**vars_wk), exist_ok=True)
    for entry in os.scandir('{USERPROFILE}\\Desktop'.format(**vars_wk['Env'])):
        # JRT, RKill, Shortcut cleaner
        if re.search(r'^((JRT|RKill).*|sc-cleaner)', entry.name, re.IGNORECASE):
            shutil.move(entry.path, '{ClientDir}\\Info\\{name}'.format(name=entry.name, **vars_wk))
    run_program('rmdir "{path}"'.format(path='{ClientDir}\\Info'.format(**vars_wk)), check=False, shell=True)

def exit_script():
    # pause("Press Enter to exit...")
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

def run_hwinfo_sensors():
    _path = '{BinDir}\\HWiNFO'.format(**vars_wk)
    for bit in [32, 64]:
        # Configure
        _source = '{path}\\general.ini'.format(path=_path)
        _dest =   '{path}\\HWiNFO{bit}.ini'.format(bit=bit, path=_path)
        shutil.copy(_source, _dest)
        with open(_dest, 'a') as f:
            f.write('SensorsOnly=1\n')
            f.write('SummaryOnly=0\n')
    subprocess.Popen(vars_wk['HWiNFO'])

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

def run_xmplay():
    extract_item('XMPlay', vars_wk, silent=True)
    subprocess.Popen([vars_wk['XMPlay'], '{BinDir}\\XMPlay\\music.7z'.format(**vars_wk)])

def uninstall_eset():
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        _path = '{PROGRAMFILES(X86)}\\ESET'.format(**vars_wk['Env'])
    else:
        _path = '{PROGRAMFILES}\\ESET'.format(**vars_wk['Env'])
    if os.path.exists('{path}\\ESET Online Scanner'.format(path=_path)):
        try:
            print_info('* Uninstalling ESET Online Scanner', vars_wk['LogFile'])
            run_program('"{path}\\ESET Online Scanner\\OnlineScannerUninstaller.exe" -s'.format(path=_path))
            shutil.rmtree('{path}\\ESET Online Scanner'.format(path=_path))
            run_program('rmdir "{path}"'.format(path=_path), check=False)
        except:
            print_error('ERROR: Failed to uninstall ESET Online Scanner.', vars_wk['LogFile'])

def uninstall_mbam():
    if 'PROGRAMFILES(X86)' in vars_wk['Env']:
        _path = '{PROGRAMFILES(X86)}\\Malwarebytes Anti-Malware'.format(**vars_wk['Env'])
    else:
        _path = '{PROGRAMFILES}\\Malwarebytes Anti-Malware'.format(**vars_wk['Env'])
    if os.path.exists('{path}'.format(path=_path)):
        print_warning('* Malwarebytes Anti-Malware installed.', vars_wk['LogFile'])
        if ask('  Uninstall?', vars_wk['LogFile']):
            try:
                run_program('"{path}\\unins000.exe" /SILENT'.format(path=_path))
                run_program('rmdir "{path}"'.format(path=_path), check=False)
            except:
                print_error('ERROR: Failed to uninstall Malwarebytes Anti-Malware.', vars_wk['LogFile'])

def uninstall_sas():
    # It is always in programfiles (not x86) ??
    _path = '{PROGRAMFILES}\\SUPERAntiSpyware'.format(**vars_wk['Env'])
    if os.path.exists(_path):
        print_warning('* SUPERAntiSpyware installed.', vars_wk['LogFile'])
        if ask('  Uninstall?', vars_wk['LogFile']):
            try:
                run_program('{path}\\Uninstall.exe'.format(path=_path))
                run_program('rmdir "{path}"'.format(path=_path), check=False)
            except:
                print_error('ERROR: Failed to uninstall SUPERAntiSpyware.', vars_wk['LogFile'])

def update_clock():
    # Set Timezone and sync clock
    print_info('* Updating system clock', vars_wk['LogFile'])
    try:
        run_program('tzutil /s "Pacific Standard Time"', check=False)
        run_program('net stop w32ime', check=False)
        run_program('w32tm /config /syncfromflags:manual /manualpeerlist:"us.pool.ntp.org time.nist.gov time.windows.com"', check=False)
        run_program('net start w32ime', check=False)
        run_program('w32tm /resync /nowait', check=False)
    except:
        print_error('ERROR: Failed to update system clock to PST/PDT', vars_wk['LogFile'])

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
    print_info('Starting Software Checklist for Ticket #{TicketNumber}\n'.format(**vars_wk), vars_wk['LogFile'])
    
    # Cleanup
    cleanup_desktop()
    cleanup_adwcleaner()
    uninstall_eset()
    uninstall_mbam()
    uninstall_sas()
    
    # Last-minute backups and adjustments
    update_clock()
    backup_power_plans()
    backup_registry()
    run_siv()
    run_produkey()
    
    ## System information ##
    get_user_data_summary()
    get_os_info()
    if 'The machine is permanently activated.' not in vars_wk['Activation']:
        subprocess.Popen('slui')
    get_free_space()
    get_installed_ram()
    get_battery_info()
    
    # Play audio, show devices, and open Windows updates
    subprocess.Popen('devmgmt.msc', shell=True)
    run_hwinfo_sensors()
    if vars_wk['Version'] == '10':
        subprocess.Popen('control /name Microsoft.WindowsUpdate', shell=True)
    else:
        subprocess.Popen('wuapp', shell=True)
    sleep(3)
    run_xmplay()
    
    # Upload info
    upload_info()
    
    # Done
    print_standard('\nDone.', vars_wk['LogFile'])
    pause('Press Enter exit...')
    
    # Open log
    extract_item('Notepad2', vars_wk)
    subprocess.Popen([vars_wk['Notepad2'], vars_wk['LogFile']])
    
    # Quit
    kill_process('caffeine.exe')
    exit_script()