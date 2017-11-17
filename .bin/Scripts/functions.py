# Wizard Kit: Init

import os
import partition_uids
import psutil
import re
import shutil
import subprocess
import time
import winreg

# STATIC VARIABLES
ARCHIVE_PASSWORD='Abracadabra'
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'}
BACKUP_SERVERS = [
    {   'IP':       '10.0.0.10',
        'Mounted':  False,
        'Name':     'ServerOne',
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

# General functions
def ask(prompt='Kotaero!', log_file=None):
    """Prompt the user with a Y/N question, log answer, and return a bool."""
    answer = None
    prompt = prompt + ' [Y/N]: '
    while answer is None:
        tmp = input(prompt)
        if re.search(r'^y(es|)$', tmp):
            answer = True
        elif re.search(r'^n(o|ope|)$', tmp):
            answer = False
    if log_file is not None:
        with open(log_file, 'a') as f:
            if answer:
                f.write('{prompt}Yes\n'.format(prompt=prompt))
            else:
                f.write('{prompt}No\n'.format(prompt=prompt))
    return answer

def assign_volume_letters():
    """Assign a drive letter for all attached volumes."""
    with open(diskpart_script, 'w') as script:
        script.write('list volume\n')
    process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
    with open(diskpart_script, 'w') as script:
        for tmp in re.findall(r'Volume (\d+)\s+([A-Za-z]?)\s+', process_return.stdout.decode()):
            if tmp[1] == '':
                script.write('select volume {number}\n'.format(number=tmp[0]))
                script.write('assign\n')
    try:
        run_program('diskpart /s {script}'.format(script=diskpart_script))
    except:
        pass

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

def extract_item(item=None, vars_wk=None, filter='', silent=False):
    """Extract item from .cbin into .bin."""
    if item is None or vars_wk is None:
        raise Exception
    vars_wk['SevenZip'] = '{BinDir}\\7-Zip\\7za.exe'.format(**vars_wk)
    if vars_wk['Arch'] == 64:
        vars_wk['SevenZip'] = vars_wk['SevenZip'].replace('7za.exe', '7za64.exe')
    _cmd = '{SevenZip} x -aos -bso0 -bse0 -p{ArchivePassword} -o"{BinDir}\\{item}" "{CBinDir}\\{item}.7z" {filter}'.format(item=item, filter=filter, **vars_wk)
    if not silent:
        print_standard('Extracting "{item}"...'.format(item=item))
    try:
        run_program(_cmd, shell=True)
    except subprocess.CalledProcessError:
        print_warning('WARNING: Errors encountered while exctracting data', log_file=vars_wk['LogFile'])

def find_windows_image(filename=None):
    """Search for an image file on local and network drives and return a dict."""
    image = {}

    # Bail early
    if filename is None:
        raise Exception('Filename not specified.')

    # Search local source
    process_return = run_program('mountvol')
    for tmp in re.findall(r'.*([A-Za-z]):\\', process_return.stdout.decode()):
        for ext in ['esd', 'wim', 'swm']:
            if os.path.isfile('{drive}:\\images\\{filename}.{ext}'.format(drive=tmp[0], ext=ext, filename=filename)):
                image['Ext'] = ext
                image['File'] = '{drive}:\\images\\{filename}'.format(drive=tmp[0], filename=filename)
                image['Glob'] = '--ref="{File}*.swm"'.format(**image) if ext == 'swm' else ''
                image['Source'] = tmp[0]
                break

    # Check for network source (if necessary)
    if not any(image):
        if not WINDOWS_SERVER['Mounted']:
            mount_windows_share()
        for ext in ['esd', 'wim', 'swm']:
            if os.path.isfile('\\\\{IP}\\{Share}\\images\\{filename}.{ext}'.format(ext=ext, filename=filename, **WINDOWS_SERVER)):
                image['Ext'] = ext
                image['File'] = '\\\\{IP}\\{Share}\\images\\{filename}'.format(filename=filename, **WINDOWS_SERVER)
                image['Glob'] = '--ref="{File}*.swm"'.format(**image) if ext == 'swm' else ''
                image['Source'] = None
                break
    
    # Display image to be used (if any) and return
    if any(image):
        print_info('Using image: {File}.{Ext}'.format(**image))
    return image

def format_gpt(disk=None, windows_family=None):
    """Format disk for use as a Windows OS drive using the GPT (UEFI) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')
    if windows_family is None:
        raise Exception('No Windows family provided.')

    # Format drive
    print_info('Drive will use a GPT (UEFI) layout.')
    with open(diskpart_script, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')
        script.write('convert gpt\n')

        # Windows RE tools partitions (Windows 8+)
        if re.search(r'^(8|10)', windows_family):
            script.write('create partition primary size=300\n')
            script.write('format quick fs=ntfs label="Windows RE tools"\n')
            script.write('assign letter="T"\n')
            script.write('set id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"\n')
            script.write('gpt attributes=0x8000000000000001\n')

        # System partition
        script.write('create partition efi size=260\n') # NOTE: Allows for Advanced Format 4K drives
        script.write('format quick fs=fat32 label="System"\n')
        script.write('assign letter="S"\n')

        # Microsoft Reserved (MSR) partition
        script.write('create partition msr size=128\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format quick fs=ntfs label="Windows"\n')
        script.write('assign letter="W"\n')

    # Run script
    print('  Formatting drive...')
    run_program('diskpart /s {script}'.format(script=diskpart_script))
    time.sleep(2)

def format_mbr(disk=None):
    """Format disk for use as a Windows OS drive using the MBR (legacy) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')

    # Format drive
    print_info('Drive will use a MBR (legacy) layout.')
    with open(diskpart_script, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')

        # System partition
        script.write('create partition primary size=100\n')
        script.write('format fs=ntfs quick label="System Reserved"\n')
        script.write('active\n')
        script.write('assign letter=s\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format fs=ntfs quick label="Windows"\n')
        script.write('assign letter=w\n')

    # Run script
    print('  Formatting drive...')
    run_program('diskpart /s {script}'.format(script=diskpart_script))
    time.sleep(2)

def get_attached_disk_info():
    """Get details about the attached disks and return a list of dicts."""
    disks = []
    # print_info('Getting drive info...')

    # Assign all the letters
    assign_volume_letters()

    # Get disk numbers
    with open(diskpart_script, 'w') as script:
        script.write('list disk\n')
    process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
    for tmp in re.findall(r'Disk (\d+)\s+\w+\s+(\d+\s+\w+)', process_return.stdout.decode()):
        disks.append({'Number': tmp[0], 'Size': human_readable_size(tmp[1])})

    # Get disk details
    for disk in disks:
        # Get partition style
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('uniqueid disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        if re.findall(r'Disk ID: {[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+}', process_return.stdout.decode()):
            disk['Table'] = 'GPT'
        elif re.findall(r'Disk ID: 00000000', process_return.stdout.decode()):
            disk['Table'] = 'RAW'
        elif re.findall(r'Disk ID: [A-Z0-9]+', process_return.stdout.decode()):
            disk['Table'] = 'MBR'
        else:
            disk['Table'] = 'Unknown'

        # Get disk name/model and physical details
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('detail disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        tmp = process_return.stdout.decode().strip().splitlines()
        # Remove empty lines and those without a ':' and split each remaining line at the ':' to form a key/value pair
        tmp = [s.strip() for s in tmp if s.strip() != '']
        # Set disk name
        disk['Name'] = tmp[4]
        tmp = [s.split(':') for s in tmp if ':' in s]
        # Add new key/value pairs to the disks variable
        disk.update({key.strip(): value.strip() for (key, value) in tmp})

        # Get partition info for disk
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('list partition\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        disk['Partitions'] = []
        for tmp in re.findall(r'Partition\s+(\d+)\s+\w+\s+(\d+\s+\w+)\s+', process_return.stdout.decode().strip()):
            disk['Partitions'].append({'Number': tmp[0], 'Size': human_readable_size(tmp[1])})
        for par in disk['Partitions']:
            # Get partition details
            with open(diskpart_script, 'w') as script:
                script.write('select disk {Number}\n'.format(**disk))
                script.write('select partition {Number}\n'.format(**par))
                script.write('detail partition\n')
            process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
            for tmp in re.findall(r'Volume\s+\d+\s+(\w|RAW)\s+', process_return.stdout.decode().strip()):
                if tmp == 'RAW':
                    par['FileSystem'] = 'RAW'
                else:
                    par['Letter'] = tmp
                    try:
                        process_return2 = run_program('fsutil fsinfo volumeinfo {Letter}:'.format(**par))
                        for line in process_return2.stdout.decode().splitlines():
                            line = line.strip()
                            # Get partition name
                            match = re.search(r'Volume Name\s+:\s+(.*)$', line)
                            if match:
                                par['Name'] = match.group(1).strip()
                            # Get filesystem type
                            match = re.search(r'File System Name\s+:\s+(.*)$', line)
                            if match:
                                par['FileSystem'] = match.group(1).strip()
                        usage = shutil.disk_usage('{Letter}:\\'.format(Letter=tmp))
                        par['Used Space'] = human_readable_size(usage.used)
                    except subprocess.CalledProcessError:
                        par['FileSystem'] = 'Unknown'
            # Get MBR type / GPT GUID for extra details on "Unknown" partitions
            for tmp in re.findall(r'Type\s+:\s+(\S+)', process_return.stdout.decode().strip()):
                par['Type'] = tmp
                uid = partition_uids.lookup_guid(tmp)
                if uid is not None:
                    par.update({
                        'Description': uid.get('Description', ''),
                        'OS': uid.get('OS', '')})
            # Ensure the Name has been set
            if 'Name' not in par:
                par['Name'] = ''
            if 'FileSystem' not in par:
                par['FileSystem'] = 'Unknown'

    # Done
    return disks

def get_free_space_info():
    """Get free space info for all fixed volumes and return a list of lists."""
    drives = run_program('fsutil fsinfo drives', check=False)
    drives = drives.stdout.decode()
    drives = drives.replace('Drives: ', '').replace('\\', '').split()
    _return = []
    for drive in sorted(drives):
        _out = run_program('fsutil fsinfo drivetype {drive}'.format(drive=drive))
        _drive_type = _out.stdout.decode()
        if re.search(r'Fixed Drive', _drive_type, re.IGNORECASE):
            try:
                _out = run_program('fsutil volume diskfree {drive}'.format(drive=drive))
                _out = _out.stdout.decode().splitlines()
                _free = int(re.sub(r'.*:\s+(.*)', r'\1', _out[0]))
                _total = int(re.sub(r'.*:\s+(.*)', r'\1', _out[1]))
                _str = '{percent:>6.2f}% Free  ({free} / {total})'.format(
                    percent = _free/_total,
                    free = human_readable_size(_free, 2),
                    total = human_readable_size(_total, 2))
                _return.append([drive, _str])
            except subprocess.CalledProcessError:
                pass
    return _return

def get_user_data_size_info(vars_wk=None):
    """Get size of user folders for all users and return a dict of dicts."""
    if vars_wk is None:
        raise Exception
    users = {}
    TMP_HIVE_PATH = 'HKU\\wk_tmp'
    
    # Extract and configure du
    extract_item('SysinternalsSuite', vars_wk, filter='du*', silent=True)
    du = '{BinDir}\\SysinternalsSuite\\du.exe'.format(**vars_wk)
    if vars_wk['Arch'] == 64:
        du = du.replace('.exe', '64.exe')
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\Du')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Sysinternals\Du', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'EulaAccepted', 0, winreg.REG_DWORD, 1)
    
    try:
        # Get SIDs
        out = run_program('wmic useraccount get sid')
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
                out = run_program(du, ['-nobanner', '-q', users[u]['ProfileImagePath']])
                size = out.stdout.decode().splitlines()[4]
                size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                size = size.replace(',', '')
                size = human_readable_size(size)
                size_str = '{folder:<20} {size:>10} ({path})'.format(folder='Profile', size=size, path=users[u]['ProfileImagePath'])
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
                                    out = run_program(du, ['-nobanner', '-q', folder_path])
                                    size = out.stdout.decode().splitlines()[4]
                                    size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                                    size = size.replace(',', '')
                                    size = human_readable_size(size)
                                    str = '{folder:<20} {size:>10} ({path})'.format(folder=folder, size=size, path=folder_path)
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
                            out = run_program(du, ['-nobanner', '-q', folder_path])
                            size = out.stdout.decode().splitlines()[4]
                            size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                            size = size.replace(',', '')
                            size = human_readable_size(size)
                            str = '{folder:<20} {size:>10} ({path})'.format(folder=folder, size=size, path=folder_path)
                            users[u]['Shell Folders'][folder] = str
                        except subprocess.CalledProcessError:
                            # Failed to get folder size
                            pass
        
            # Extra folder sizes
            for folder in EXTRA_FOLDERS:
                folder_path = '{ProfileImagePath}\\{folder}'.format(folder=folder, **users[u])
                if os.path.exists(folder_path):
                    try:
                        out = run_program(du, ['-nobanner', '-q', folder_path])
                        size = size.stdout.decode().splitlines()[4]
                        size = re.sub(r'Size:\s+([\d,]+)\sbytes$', r'\1', size)
                        size = size.replace(',', '')
                        size = human_readable_size(size)
                        str = '{folder:<20} {size:>10} ({path})'.format(folder=folder, size=size, path=folder_path)
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

def menu_select(title='~ Untitled Menu ~', main_entries=[], action_entries=[], prompt='Please make a selection', secret_exit=False):
    """Display options in a menu for user and return selected option as a str."""
    # Bail early
    if (len(main_entries) + len(action_entries) == 0):
        raise Exception("MenuError: No items given")

    # Build menu
    menu_splash = '{title}\n\n'.format(title=title)
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
            if ('Disabled' in entry):
                menu_splash += '{YELLOW}{number:>{mwidth}}: {name} (DISABLED){CLEAR}\n'.format(number=i+1, mwidth=len(str(len(main_entries))), name=entry.get('Display Name', entry['Name']), **COLORS)
            else:
                valid_answers.append(str(i+1))
                menu_splash += '{number:>{mwidth}}: {name}\n'.format(number=i+1, mwidth=len(str(len(main_entries))), name=entry.get('Display Name', entry['Name']))
        menu_splash += '\n'

    # Add action entries
    if (len(action_entries) > 0):
        for entry in action_entries:
            # Add Spacer
            if ('CRLF' in entry):
                menu_splash += '\n'
            valid_answers.append(entry['Letter'])
            menu_splash += '{letter:>{mwidth}}: {name}\n'.format(letter=entry['Letter'].upper(), mwidth=len(str(len(action_entries))), name=entry['Name'])
        menu_splash += '\n'

    answer = ''

    while (answer.upper() not in valid_answers):
        os.system('cls')
        print(menu_splash)
        answer = input('{prompt}: '.format(prompt=prompt))

    return answer.upper()

def mount_backup_shares():
    """Mount the backup shares unless labeled as already mounted."""
    for server in BACKUP_SERVERS:
        # Blindly skip if we mounted earlier
        if server['Mounted']:
            continue
        else:
            try:
                # Test connection
                run_program('ping -w 800 -n 2 {IP}'.format(**server))

                # Mount
                run_program('net use \\\\{IP}\\{Share} /user:{User} {Pass}'.format(**server))
                print_info('Mounted {Name}'.format(**server))
                server['Mounted'] = True
            except subprocess.CalledProcessError:
                print_error('Failed to mount \\\\{Name}\\{Share}, {IP} unreachable.'.format(**server))
                time.sleep(1)
            except:
                print_warning('Failed to mount \\\\{Name}\\{Share} ({IP})'.format(**server))
                time.sleep(1)

def mount_windows_share():
    """Mount the Windows images share unless labeled as already mounted."""
    # Blindly skip if we mounted earlier
    if WINDOWS_SERVER['Mounted']:
        return None
    else:
        try:
            # Test connection
            run_program('ping -w 800 -n 2 {IP}'.format(**WINDOWS_SERVER))
            # Mount
            run_program('net use \\\\{IP}\\{Share} /user:{User} {Pass}'.format(**WINDOWS_SERVER))
            print_info('Mounted {Name}'.format(**WINDOWS_SERVER))
            WINDOWS_SERVER['Mounted'] = True
        except subprocess.CalledProcessError:
            print_error('Failed to mount \\\\{Name}\\{Share}, {IP} unreachable.'.format(**WINDOWS_SERVER))
            time.sleep(1)
        except:
            print_warning('Failed to mount \\\\{Name}\\{Share}'.format(**WINDOWS_SERVER))
            time.sleep(1)

def pause(prompt='Press Enter to continue... '):
    """Simple pause implementation."""
    input(prompt)

def print_error(message='Generic error', log_file=None, **kwargs):
    """Prints message to screen in RED and writes it to log_file if provided."""
    print('{RED}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))
    if log_file is not None:
        with open(log_file, 'a') as f:
            f.write(message + '\n')

def print_info(message='Generic info', log_file=None, **kwargs):
    """Prints message to screen in BLUE and writes it to log_file if provided."""
    print('{BLUE}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))
    if log_file is not None:
        with open(log_file, 'a') as f:
            f.write(message + '\n')

def print_warning(message='Generic warning', log_file=None, **kwargs):
    """Prints message to screen in YELLOW and writes it to log_file if provided."""
    print('{YELLOW}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))
    if log_file is not None:
        with open(log_file, 'a') as f:
            f.write(message + '\n')

def print_standard(message='Generic info', log_file=None, **kwargs):
    """Prints message to screen and writes it to log_file if provided."""
    print('{message}'.format(message=message, **COLORS, **kwargs))
    if log_file is not None:
        with open(log_file, 'a') as f:
            f.write(message + '\n')

def print_success(message='Generic success', log_file=None, **kwargs):
    """Prints message to screen in GREEN and writes it to log_file if provided."""
    print('{GREEN}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))
    if log_file is not None:
        with open(log_file, 'a') as f:
            f.write(message + '\n')

def remove_volume_letters(keep=None):
    """Remove the assigned drive letter for all attached volumes."""
    with open(diskpart_script, 'w') as script:
        script.write('list volume\n')
    process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
    with open(diskpart_script, 'w') as script:
        for tmp in re.findall(r'Volume (\d+)\s+([A-Za-z]?)\s+', process_return.stdout.decode()):
            if tmp[1] != '' and tmp[1] != keep:
                script.write('select volume {number}\n'.format(number=tmp[0]))
                script.write('remove\n')
    try:
        run_program('diskpart /s {script}'.format(script=diskpart_script))
    except:
        pass

def run_program(cmd=None, args=[], check=True, pipe=True, shell=False):
    """Run program and return a subprocess.CompletedProcess instance."""
    if cmd is None:
        raise Exception('No program passed.')
    
    _cmd = cmd
    if len(args) > 0:
        _cmd = [cmd] + args
    
    if pipe:
        process_return = subprocess.run(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check, shell=shell)
    else:
        process_return = subprocess.run(_cmd, check=check, shell=shell)

    return process_return

def select_backup(ticket):
    """Find any backups for the ticket stored on one of the BACKUP_SERVERS. Returns path as a os.DirEntry."""
    _backups = []
    mount_backup_shares()
    for server in BACKUP_SERVERS:
        if server['Mounted']:
            for d in os.scandir('\\\\{IP}\\{Share}'.format(**server)):
                if d.is_dir() and re.match('^{}'.format(ticket), d.name):
                    _backups.append({'Name': '{s_name}: {backup}'.format(s_name=server['Name'], backup=d.name), 'Dir': d})
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]

    # Select backup path
    if len(_backups) > 0:
        selection = menu_select('Which backup are we using?', _backups, actions)
        if selection == 'Q':
            return None
        else:
            return _backups[int(selection)-1]['Dir']
    else:
        print_error('No backups found for ticket: {ticket}.'.format(ticket=ticket))
        return None

def select_destination():
    """Select backup destination and return a dict."""
    # Build menu
    dests = []
    for server in BACKUP_SERVERS:
         if server['Mounted']:
            dests.append(server)
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Size check
    for dest in dests:
        if 'IP' in dest:
            dest['Usage'] = shutil.disk_usage('\\\\{IP}\\{Share}'.format(**dest))
        else:
            dest['Usage'] = shutil.disk_usage('{Letter}:\\'.format(**dest))
        dest['Free Space'] = human_readable_size(dest['Usage'].free)
        dest['Display Name'] = '{Name} ({Free Space} available)'.format(**dest)

    # Show menu or bail
    if len(dests) > 0:
        selection = menu_select('Where are we backing up to?', dests, actions)
        if selection == 'M':
            return None
        else:
            return dests[int(selection)-1]
    else:
        print_warning('No backup destinations found.')
        return None

def select_disk(prompt='Which disk?'):
    """Select a disk from the attached disks and return the disk number as an int."""
    disks = get_attached_disk_info()

    # Build menu
    disk_options = []
    for disk in disks:
        display_name = '{Size}\t[{Table}] ({Type}) {Name}'.format(**disk)
        if len(disk['Partitions']) > 0:
            pwidth=len(str(len(disk['Partitions'])))
            for par in disk['Partitions']:
                # Show unsupported partition(s) in RED
                par_skip = False
                if 'Letter' not in par or re.search(r'(RAW|Unknown)', par['FileSystem']):
                    par_skip = True
                if par_skip:
                    display_name += COLORS['YELLOW']

                # Main text
                display_name += '\n\t\t\tPartition {Number:>{pwidth}}: {Size} ({FileSystem})'.format(pwidth=pwidth, **par)
                if par['Name'] != '':
                    display_name += '\t"{Name}"'.format(**par)

                # Clear color (if set above)
                if par_skip:
                    display_name += COLORS['CLEAR']
        else:
            display_name += '{YELLOW}\n\t\t\tNo partitions found.{CLEAR}'.format(**COLORS)
        disk_options.append({'Name': display_name, 'Disk': disk})
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Menu loop
    selection = menu_select(prompt, disk_options, actions)

    if (selection.isnumeric()):
        return disk_options[int(selection)-1]['Disk']
    elif (selection == 'M'):
        # -1 here means cancel
        return -1

def select_minidump_path():
    """Have the user select from all found MiniDump locations and return a dict."""
    dumps = []

    # Assign volume letters first
    assign_volume_letters()

    # Search for minidumps
    tmp = run_program('mountvol')
    tmp = [d for d in re.findall(r'.*([A-Za-z]):\\', tmp.stdout.decode())]
    # Remove RAMDisk letter
    if 'X' in tmp:
        tmp.remove('X')
    for drive in tmp:
        if os.path.exists('{drive}:\\Windows\\MiniDump'.format(drive=drive)):
            dumps.append({'Name': '{drive}:\\Windows\\MiniDump'.format(drive=drive)})

    # Check results before showing menu
    if len(dumps) == 0:
        print_error('  No BSoD / MiniDump paths found')
        time.sleep(2)
        return None

    # Menu
    selection = menu_select('Which BSoD / MiniDump path are we scanning?', dumps, [])
    return dumps[int(selection) - 1]['Name']

def select_windows_version():
    """Select Windows version and return a dict."""
    versions = [
        {'Name': 'Windows 7 Home Basic',
            'ImageFile': 'Win7',
            'ImageName': 'Windows 7 HOMEBASIC',
            'Family': '7'},
        {'Name': 'Windows 7 Home Premium',
            'ImageFile': 'Win7',
            'ImageName': 'Windows 7 HOMEPREMIUM',
            'Family': '7'},
        {'Name': 'Windows 7 Professional', 
            'ImageFile': 'Win7', 
            'ImageName': 'Windows 7 PROFESSIONAL', 
            'Family': '7'},
        {'Name': 'Windows 7 Ultimate', 
            'ImageFile': 'Win7', 
            'ImageName': 'Windows 7 ULTIMATE', 
            'Family': '7'},

        {'Name': 'Windows 8.1', 
            'ImageFile': 'Win8', 
            'ImageName': 'Windows 8.1', 
            'Family': '8',
            'CRLF': True},
        {'Name': 'Windows 8.1 Pro', 
            'ImageFile': 'Win8', 
            'ImageName': 'Windows 8.1 Pro', 
            'Family': '8'},

        {'Name': 'Windows 10 Home', 
            'ImageFile': 'Win10', 
            'ImageName': 'Windows 10 Home', 
            'Family': '10',
            'CRLF': True},
        {'Name': 'Windows 10 Pro', 
            'ImageFile': 'Win10', 
            'ImageName': 'Windows 10 Pro', 
            'Family': '10'},
    ]
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Menu loop
    selection = menu_select('Which version of Windows are we installing?', versions, actions)

    if selection.isnumeric():
        return versions[int(selection)-1]
    elif selection == 'M':
        return None

def sleep(seconds=2):
    time.sleep(seconds)

def stay_awake(vars_wk=None):
    """Prevent the system from sleeping or hibernating."""
    if vars_wk is None:
        raise Exception
    # Bail if caffeine is already running
    for proc in psutil.process_iter():
        if proc.name() == 'caffeine.exe':
            return
    # Extract and run
    extract_item('caffeine', vars_wk, silent=True)
    try:
        subprocess.Popen('"{BinDir}\\caffeine\\caffeine.exe"'.format(**vars_wk))
    except:
        print_error('ERROR: No caffeine available; please set the power setting to High Performace.')

def upload_data(path=None, file=None, vars_wk=None):
    """Add CLIENT_INFO_SERVER to authorized connections and upload file."""
    # Bail early
    if path is None or file is None or vars_wk is None:
        raise Exception
    
    extract_item('PuTTY', vars_wk, filter='WK.ppk psftp.exe', silent=True)
    
    # Authorize connection to the server
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\SimonTatham\PuTTY\SshHostKeys')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\SimonTatham\PuTTY\SshHostKeys', access=winreg.KEY_WRITE) as _key:
        winreg.SetValueEx(_key, 'rsa2@22:10.0.0.10', 0, winreg.REG_SZ, r'0x10001,0xf60757b7656263622b3c17b2ec1a9bd74c555fe927b5e571928007cf944a98113db2434a33c782e8b51447ceb7cd0b30475f0d988ef23af75a5b48eaa8edad478489b314837fd5134a8059084ae6bafdb4a3eb759afad7474027c81773dc233ea4c4e46f6f5b32a58672b0e541613ac6eb231715fd5ffc28f237b66ef9ed18deff232e83acc1ecdf10794d11344ac68035d48d0bcc0c83f76b1fe9d5d16bb46d9906ce4e0214ba03cec411b2801a238e891e3eedc7ed4b41a81f0e228c0a4b7efedad8c10b982d01098628f8c4e3166e0b3a19fef11dc8600ceedbd19d6844d5e9c7147b4f64ec58b04dd9fb571a0909d2847894fbf9694415eb89df0a2b6fb1')
    
    # Write batch file
    with open('{TmpDir}\\psftp.batch'.format(**vars_wk), 'w', encoding='ascii') as f:
        f.write('lcd "{path}"\n'.format(path=path))
        f.write('cd "{Share}"\n'.format(**CLIENT_INFO_SERVER))
        f.write('put "{file}"\n'.format(file=file))
    
    # Upload Info
    _cmd = [
        '{BinDir}\\PuTTY\\PSFTP.EXE'.format(**vars_wk),
        '-noagent',
        '-i', '{BinDir}\\PuTTY\WK.ppk'.format(**vars_wk),
        '{User}@{IP}'.format(**CLIENT_INFO_SERVER),
        '-b', '{TmpDir}\\psftp.batch'.format(**vars_wk)]
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

def kill_process(name=None):
    """Kill any running caffeine.exe processes."""
    if name is None:
        raise Exception
    for proc in psutil.process_iter():
        if proc.name() == name:
            proc.kill()

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
            time.sleep(1)

# Init functions
def init_vars_wk():
    """Sets common variables and returns a dict."""
    print('Initializing...')
    # Find base path
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
        print_error('".bin" not found.')
        pause('Press any key to exit...')
        quit()
    
    # Set vars
    _vars = {
        'BaseDir':      _base,
        'Date':         time.strftime("%Y-%m-%d"),
        'Date-Time':    time.strftime("%Y-%m-%d_%H%M_%z"),
        'Env':          os.environ.copy()
    }
    _vars['ArchivePassword'] =  ARCHIVE_PASSWORD
    _vars['BinDir'] =           '{BaseDir}\\.bin'.format(**_vars)
    _vars['CBinDir'] =          '{BaseDir}\\.cbin'.format(**_vars)
    _vars['ClientDir'] =        '{SYSTEMDRIVE}\\WK'.format(**_vars['Env'])
    _vars['LogDir'] =           '{ClientDir}\\Info\\{Date}'.format(**_vars)
    _vars['TmpDir'] =           '{BinDir}\\tmp'.format(**_vars)
    os.makedirs(_vars['TmpDir'], exist_ok=True)
    
    return _vars

def init_vars_os():
    """Sets variables relating to the installed OS and returns a dict."""
    print('Checking OS...')
    _vars_os = {}
    _env = os.environ.copy()
    
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
    
    # Determine Windows version
    if _vars_os['CurrentVersion'] == '6.0':
        _vars_os['Version'] = 'Vista'
    elif _vars_os['CurrentVersion'] == '6.1':
        _vars_os['Version'] = '7'
    elif _vars_os['CurrentVersion'] == '6.2':
        _vars_os['Version'] = '8'
    elif _vars_os['CurrentVersion'] == '6.3':
        if int(_vars_os['CurrentBuildNumber']) <= 9600:
            _vars_os['Version'] = '8'
        elif int(_vars_os['CurrentBuildNumber']) >= 10240:
            _vars_os['Version'] = '10'
    
    # Determine OS bit depth
    _vars_os['Arch'] = 32
    if 'PROGRAMFILES(X86)' in _env:
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
    # === 10 v1607 "Anniversary Update" "Redstone 1" ==
    # 6.3.14393
    # === 10 v???? "Redstone 2" ==
    # 6.3.?????
    
    # Determine bootup type
    _vars_os['SafeMode'] = False
    if 'SAFEBOOT_OPTION' in _env:
        _vars_os['SafeMode'] = True
    
    # Determine activation status
    if _vars_os['SafeMode']:
        _vars_os['Activation'] = 'Activation status unavailable in safe mode'
    else:
        _out = run_program('cscript /nologo {SYSTEMROOT}\\System32\\slmgr.vbs /xpr'.format(**_env))
        _out = _out.stdout.decode().splitlines()
        _out = [l for l in _out if re.match(r'^\s', l)]
        if len(_out) > 0:
            _vars_os['Activation'] = re.sub(r'^\s+', '', _out[0])
        else:
            _vars_os['Activation'] = 'Activation status unknown'
    
    return _vars_os

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
