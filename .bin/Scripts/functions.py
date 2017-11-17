# Wizard Kit: Init

import os
import partition_uids
import re
import shutil
import subprocess
import time
import winreg

# Server info
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

# Colors
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'}

# General functions
def ask(prompt='Kotaero'):
    """Prompt the user with a Y/N question and return a bool."""
    answer = None
    prompt = prompt + ' [Y/N]: '
    while answer is None:
        tmp = input(prompt)
        if re.search(r'^y(es|)$', tmp):
            answer = True
        elif re.search(r'^n(o|ope|)$', tmp):
            answer = False
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
    print_info('Getting drive info...')

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
def init_vars():
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
    _vars['BinDir'] =       '{BaseDir}\\.bin'.format(**_vars)
    _vars['ClientDir'] =    '{SYSTEMDRIVE}\\WK'.format(**_vars['Env'])
    _vars['LogDir'] =       '{ClientDir}\\Info\\{Date}'.format(**_vars)
    _vars['TmpDir'] =       '{BinDir}\\tmp'.format(**_vars)
    
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
        _out = run_program('cscript /nologo {WINDIR}\\System32\\slmgr.vbs /xpr'.format(**_env))
        _out = _out.stdout.decode().splitlines()
        _out = [l for l in _out if re.match(r'^\s', l)]
        if len(_out) > 0:
            _vars_os['Activation'] = re.sub(r'^\s+', '', _out[0])
        else:
            _vars_os['Activation'] = 'Activation status unknown'
    
    return _vars_os

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
