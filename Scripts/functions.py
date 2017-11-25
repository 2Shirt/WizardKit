# WK WinPE Functions

# Init
import os
import re
import shutil
import subprocess
import sys
import time
import winreg
os.chdir(os.path.dirname(os.path.realpath(__file__)))
bin = os.path.abspath('..\\')
sys.path.append(os.getcwd())
from functions import *
import partition_uids

# Init
BACKUP_SERVERS = [
    {   'IP':       '10.0.0.10',
        'Mounted':  False,
        'Name':     'ServerOne',
        'Share':    'Backups',
        'User':     'backup',
        'Pass':     'Abracadabra',
    },
    {   'IP':       '10.0.0.11',
        'Name':     'ServerTwo',
        'Mounted':  False,
        'Share':    'Backups',
        'User':     'backup',
        'Pass':     'Abracadabra',
    },
]
WINDOWS_SERVER = {
    'IP':           '10.0.0.10',
    'Name':         'ServerOne',
    'Mounted':      False,
    'Share':        'Windows',
    'User':         'backup',       # Using these credentials in case both the windows source and backup shares are mounted.
    'Pass':         'Abracadabra',  # This is because Windows only allows one set of credentials to be used per server at a time.
}
WINDOWS_VERSIONS = [
        {'Name': 'Windows 7 Home Basic',
            'Image File': 'Win7',
            'Image Name': 'Windows 7 HOMEBASIC',
            'Family': '7'},
        {'Name': 'Windows 7 Home Premium',
            'Image File': 'Win7',
            'Image Name': 'Windows 7 HOMEPREMIUM',
            'Family': '7'},
        {'Name': 'Windows 7 Professional', 
            'Image File': 'Win7', 
            'Image Name': 'Windows 7 PROFESSIONAL', 
            'Family': '7'},
        {'Name': 'Windows 7 Ultimate', 
            'Image File': 'Win7', 
            'Image Name': 'Windows 7 ULTIMATE', 
            'Family': '7'},

        {'Name': 'Windows 8.1', 
            'Image File': 'Win8', 
            'Image Name': 'Windows 8.1', 
            'Family': '8',
            'CRLF': True},
        {'Name': 'Windows 8.1 Pro', 
            'Image File': 'Win8', 
            'Image Name': 'Windows 8.1 Pro', 
            'Family': '8'},

        {'Name': 'Windows 10 Home', 
            'Image File': 'Win10', 
            'Image Name': 'Windows 10 Home', 
            'Family': '10',
            'CRLF': True},
        {'Name': 'Windows 10 Pro', 
            'Image File': 'Win10', 
            'Image Name': 'Windows 10 Pro', 
            'Family': '10'},
]
diskpart_script = '{tmp}\\diskpart.script'.format(tmp=os.environ['TMP'])

## Colors
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'}

class AbortError(Exception):
    pass

class BackupError(Exception):
    pass

class SetupError(Exception):
    pass

def abort_to_main_menu(message='Returning to main menu...'):
    print_warning(message)
    pause('Press Enter to return to main menu... ')
    raise AbortError

def ask(prompt='Kotaero'):
    answer = None
    prompt = prompt + ' [Y/N]: '
    while answer is None:
        tmp = input(prompt)
        if re.search(r'^y(es|)$', tmp, re.IGNORECASE):
            answer = True
        elif re.search(r'^n(o|ope|)$', tmp, re.IGNORECASE):
            answer = False
    return answer

def assign_volume_letters():
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            for vol in get_volumes():
                script.write('select volume {Number}\n'.format(**vol))
                script.write('assign\n')
        run_program('diskpart /s {script}'.format(script=diskpart_script))
    except subprocess.CalledProcessError:
        pass

def backup_partition(bin=None, disk=None, par=None):
    # Bail early
    if bin is None:
        raise Exception('bin path not specified.')
    if disk is None:
        raise Exception('Disk not specified.')
    if par is None:
        raise Exception('Partition not specified.')
    
    print('    Partition {Number} Backup...\t\t'.format(**par), end='', flush=True)
    if par['Number'] in disk['Bad Partitions']:
        print_warning('Skipped.')
    else:
        cmd = '{bin}\\wimlib\\wimlib-imagex capture {Letter}:\\ "{Image Path}\\{Image File}" "{Image Name}" "{Image Name}" --compress=none'.format(bin=bin, **par)
        if par['Image Exists']:
            print_warning('Skipped.')
        else:
            try:
                os.makedirs('{Image Path}'.format(**par), exist_ok=True)
                run_program(cmd)
                print_success('Complete.')
            except subprocess.CalledProcessError as err:
                print_error('Failed.')
                par['Error'] = err.stderr.decode().splitlines()
                raise BackupError

def convert_to_bytes(size):
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

def is_valid_image(bin=None, filename=None, imagename=None):
    # Bail early
    if bin is None:
        raise Exception('bin not specified.')
    if filename is None:
        raise Exception('Filename not specified.')
    if imagename is None:
        raise Exception('Image Name not specified.')
    
    cmd = '{bin}\\wimlib\\wimlib-imagex info "{filename}" "{imagename}"'.format(bin=bin, filename=filename, imagename=imagename)
    try:
        run_program(cmd)
    except subprocess.CalledProcessError:
        print_error('Invalid image: {filename}'.format(filename=filename))
        return False
    
    return True

def find_windows_image(bin, windows_version=None):
    """Search for a Windows source image file on local drives and network drives (in that order)"""
    image = {}

    # Bail early
    if windows_version is None:
        raise Exception('Windows version not specified.')
    imagefile = windows_version['Image File']

    # Search local source
    process_return = run_program('mountvol')
    for tmp in re.findall(r'.*([A-Za-z]):\\', process_return.stdout.decode()):
        for ext in ['esd', 'wim', 'swm']:
            filename = '{drive}:\\images\\{imagefile}'.format(drive=tmp[0], imagefile=imagefile)
            filename_ext = '{filename}.{ext}'.format(filename=filename, ext=ext)
            if os.path.isfile(filename_ext):
                if is_valid_image(bin, filename_ext, windows_version['Image Name']):
                    image['Ext'] = ext
                    image['File'] = filename
                    image['Glob'] = '--ref="{File}*.swm"'.format(**image) if ext == 'swm' else ''
                    image['Source'] = tmp[0]
                    break

    # Check for network source (if necessary)
    if not any(image):
        if not WINDOWS_SERVER['Mounted']:
            mount_windows_share()
        for ext in ['esd', 'wim', 'swm']:
            filename = '\\\\{IP}\\{Share}\\images\\{imagefile}'.format(imagefile=imagefile, **WINDOWS_SERVER)
            filename_ext = '{filename}.{ext}'.format(filename=filename, ext=ext)
            if os.path.isfile(filename_ext):
                if is_valid_image(bin, filename_ext, windows_version['Image Name']):
                    image['Ext'] = ext
                    image['File'] = filename
                    image['Glob'] = '--ref="{File}*.swm"'.format(**image) if ext == 'swm' else ''
                    image['Source'] = None
                    break
    
    # Display image to be used (if any) and return
    if any(image):
        print_info('Using image: {File}.{Ext}'.format(**image))
        return image
    else:
        print_error('Failed to find Windows source image for {winver}'.format(winver=windows_version['Name']))
        abort_to_main_menu('Aborting Windows setup')

def format_gpt(disk=None, windows_family=None):
    """Format disk for use as a Windows OS drive using the GPT (UEFI) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')
    if windows_family is None:
        raise Exception('No Windows family provided.')

    # Format drive
    # print_info('Drive will use a GPT (UEFI) layout.')
    with open(diskpart_script, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')
        script.write('convert gpt\n')

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

        # Recovery Tools partition (Windows 8+)
        if re.search(r'^(8|10)', windows_family):
            script.write('shrink minimum=500\n')
            script.write('create partition primary\n')
            script.write('format quick fs=ntfs label="Recovery Tools"\n')
            script.write('assign letter="T"\n')
            script.write('set id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"\n')
            script.write('gpt attributes=0x8000000000000001\n')

    # Run script
    run_program('diskpart /s {script}'.format(script=diskpart_script))
    time.sleep(2)

def format_mbr(disk=None, windows_family=None):
    """Format disk for use as a Windows OS drive using the MBR (legacy) layout."""

    # Bail early
    if disk is None:
        raise Exception('No disk provided.')
    if windows_family is None:
        raise Exception('No Windows family provided.')

    # Format drive
    # print_info('Drive will use a MBR (legacy) layout.')
    with open(diskpart_script, 'w') as script:
        # Partition table
        script.write('select disk {number}\n'.format(number=disk['Number']))
        script.write('clean\n')

        # System partition
        script.write('create partition primary size=100\n')
        script.write('format fs=ntfs quick label="System Reserved"\n')
        script.write('active\n')
        script.write('assign letter="S"\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format fs=ntfs quick label="Windows"\n')
        script.write('assign letter="W"\n')

        # Recovery Tools partition (Windows 8+)
        if re.search(r'^(8|10)', windows_family):
            script.write('shrink minimum=500\n')
            script.write('create partition primary\n')
            script.write('format quick fs=ntfs label="Recovery"\n')
            script.write('assign letter="T"\n')
            script.write('set id=27\n')

    # Run script
    run_program('diskpart /s {script}'.format(script=diskpart_script))
    time.sleep(2)

def get_attached_disk_info():
    """Get details about the attached disks"""
    disks = []
    print_info('Getting drive info...')

    # Assign all the letters
    assign_volume_letters()

    # Get disks
    disks = get_disks()

    # Get disk details
    for disk in disks:
        # Get partition style
        disk['Table'] = get_table_type(disk)

        # Get disk name/model and physical details
        disk.update(get_disk_details(disk))

        # Get partition info for disk
        disk['Partitions'] = get_partitions(disk)
        
        for par in disk['Partitions']:
            # Get partition details
            par.update(get_partition_details(disk, par))

    # Done
    return disks

def get_boot_mode():
    boot_mode = 'Legacy'
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'System\\CurrentControlSet\\Control')
        reg_value = winreg.QueryValueEx(reg_key, 'PEFirmwareType')[0]
        if reg_value == 2:
            boot_mode = 'UEFI'
    except:
        boot_mode = 'Unknown'
    
    return boot_mode

def get_disk_details(disk=None):
    details = {}
    
    # Bail early
    if disk is None:
        raise Exception('Disk not specified.')
    
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('detail disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Remove empty lines
        tmp = [s.strip() for s in process_return.splitlines() if s.strip() != '']
        
        # Set disk name
        details['Name'] = tmp[4]
        
        # Remove lines without a ':' and split each remaining line at the ':' to form a key/value pair
        tmp = [s.split(':') for s in tmp if ':' in s]
        
        # Add key/value pairs to the details variable and return dict
        details.update({key.strip(): value.strip() for (key, value) in tmp})
    
    return details
    
def get_disks():
    disks = []
    
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            script.write('list disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Append disk numbers
        for tmp in re.findall(r'Disk (\d+)\s+\w+\s+(\d+\s+\w+)', process_return):
            _num = tmp[0]
            _size = human_readable_size(tmp[1])
            disks.append({'Number': _num, 'Size': _size})
    
    return disks

def get_partition_details(disk=None, par=None):
    details = {}
    
    # Bail early
    if disk is None:
        raise Exception('Disk not specified.')
    if par is None:
        raise Exception('Partition not specified.')
    
    # Diskpart details
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('select partition {Number}\n'.format(**par))
            script.write('detail partition\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Get volume letter or RAW status
        tmp = re.search(r'Volume\s+\d+\s+(\w|RAW)\s+', process_return)
        if tmp:
            if tmp.group(1).upper() == 'RAW':
                details['FileSystem'] = RAW
            else:
                details['Letter'] = tmp.group(1)
        
        # Remove empty lines from process_return
        tmp = [s.strip() for s in process_return.splitlines() if s.strip() != '']
        
        # Remove lines without a ':' and split each remaining line at the ':' to form a key/value pair
        tmp = [s.split(':') for s in tmp if ':' in s]
        
        # Add key/value pairs to the details variable and return dict
        details.update({key.strip(): value.strip() for (key, value) in tmp})
    
    # Get MBR type / GPT GUID for extra details on "Unknown" partitions
    guid = partition_uids.lookup_guid(details['Type'])
    if guid is not None:
        details.update({
            'Description':  guid.get('Description', ''),
            'OS':           guid.get('OS', '')})
    
    if 'Letter' in details:
        # Disk usage
        tmp = shutil.disk_usage('{Letter}:\\'.format(**details))
        details['Used Space'] = human_readable_size(tmp.used)
        
        # fsutil details
        try:
            process_return = run_program('fsutil fsinfo volumeinfo {Letter}:'.format(**details))
            process_return = process_return.stdout.decode().strip()
        except subprocess.CalledProcessError:
            pass
        else:
            # Remove empty lines from process_return
            tmp = [s.strip() for s in process_return.splitlines() if s.strip() != '']
        
            # Add "Feature" lines
            details['File System Features'] = [s.strip() for s in tmp if ':' not in s]
            
            # Remove lines without a ':' and split each remaining line at the ':' to form a key/value pair
            tmp = [s.split(':') for s in tmp if ':' in s]
            
            # Add key/value pairs to the details variable and return dict
            details.update({key.strip(): value.strip() for (key, value) in tmp})
        
    # Set Volume Name
    details['Name'] = details.get('Volume Name', '')
    
    # Set FileSystem Type
    if details.get('FileSystem', '') != 'RAW':
        details['FileSystem'] = details.get('File System Name', 'Unknown')
    
    return details

def get_partitions(disk=None):
    partitions = []
    
    # Bail early
    if disk is None:
        raise Exception('Disk not specified.')
    
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('list partition\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Append partition numbers
        for tmp in re.findall(r'Partition\s+(\d+)\s+\w+\s+(\d+\s+\w+)\s+', process_return, re.IGNORECASE):
            _num = tmp[0]
            _size = human_readable_size(tmp[1])
            partitions.append({'Number': _num, 'Size': _size})
    
    return partitions

def get_table_type(disk=None):
    _type = 'Unknown'
    
    # Bail early
    if disk is None:
        raise Exception('Disk not specified.')
    
    try:
        with open(diskpart_script, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('uniqueid disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        if re.findall(r'Disk ID: {[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+}', process_return, re.IGNORECASE):
            _type = 'GPT'
        elif re.findall(r'Disk ID: 00000000', process_return, re.IGNORECASE):
            _type = 'RAW'
        elif re.findall(r'Disk ID: [A-Z0-9]+', process_return, re.IGNORECASE):
            _type = 'MBR'
    
    return _type

def get_ticket_id():
    ticket_id = None
    while ticket_id is None:
        tmp = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([\-_]*\w+|))$', tmp):
            ticket_id = tmp
    
    return ticket_id

def get_volumes():
    vols = []
    
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            script.write('list volume\n')
        process_return = run_program('diskpart /s {script}'.format(script=diskpart_script))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Append volume numbers
        for tmp in re.findall(r'Volume (\d+)\s+([A-Za-z]?)\s+', process_return):
            vols.append({'Number': tmp[0], 'Letter': tmp[1]})
    
    return vols

def human_readable_size(size, decimals=0):
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
    """Display options in a menu for user selection"""

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
    """Mount the backup shares for use as destinations for backup image creation"""

    # Attempt to mount share(s)
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
    """Mount the Windows images share for use in Windows setup"""

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
    input(prompt)

def prep_disk_for_backup(dest=None, disk=None, ticket_id=None):
    disk['Backup Warnings'] = '\n'
    disk['Clobber Risk'] = []
    width = len(str(len(disk['Partitions'])))
    
    # Bail early
    if dest is None:
        raise Exception('Destination not provided.')
    if disk is None:
        raise Exception('Disk not provided.')
    if ticket_id is None:
        raise Exception('Ticket ID not provided.')

    # Get partition totals
    disk['Bad Partitions'] = [par['Number'] for par in disk['Partitions'] if 'Letter' not in par or re.search(r'(RAW|Unknown)', par['FileSystem'], re.IGNORECASE)]
    disk['Valid Partitions'] = len(disk['Partitions']) - len(disk['Bad Partitions'])
    
    # Bail if no valid partitions are found (those that can be imaged)
    if disk['Valid Partitions'] <= 0:
        abort_to_main_menu('  No partitions can be imaged for the selected drive')
    
    # Prep partitions
    for par in disk['Partitions']:
        if par['Number'] in disk['Bad Partitions']:
            par['Display String'] = '{YELLOW}  * Partition {Number:>{width}}:\t{Size} {FileSystem}\t\t{q}{Name}{q}\t{Description} ({OS}){CLEAR}'.format(
                width=width,
                q='"' if par['Name'] != '' else '',
                **par,
                **COLORS)
        else:
            # Update info for WIM capturing
            par['Image Name'] = str(par['Name'])
            if par['Image Name'] == '':
                par['Image Name'] = 'Unknown'
            if 'IP' in dest:
                par['Image Path'] = '\\\\{IP}\\{Share}\\{ticket}'.format(ticket=ticket_id, **dest)
            else:
                par['Image Path'] = '{Letter}:\\{ticket}'.format(ticket=ticket_id, **dest)
            par['Image File'] = '{Number}_{Image Name}'.format(**par)
            par['Image File'] = '{fixed_name}.wim'.format(fixed_name=re.sub(r'\W', '_', par['Image File']))

            # Check for existing backups
            par['Image Exists'] = False
            if os.path.exists('{Image Path}\\{Image File}'.format(**par)):
                par['Image Exists'] = True
                disk['Clobber Risk'].append(par['Number'])
                par['Display String'] = '{BLUE}  + '.format(**COLORS)
            else:
                par['Display String'] = '{CLEAR}    '.format(**COLORS)
            
            # Append rest of Display String for valid/clobber partitions
            par['Display String'] += 'Partition {Number:>{width}}:\t{Size} {FileSystem} (Used: {Used Space})\t{q}{Name}{q}{CLEAR}'.format(
                width=width,
                q='"' if par['Name'] != '' else '',
                **par,
                **COLORS)
    
    # Set description for bad partitions
    if len(disk['Bad Partitions']) > 1:
        disk['Backup Warnings'] += '{YELLOW}  * Unable to backup these partitions{CLEAR}\n'.format(**COLORS)
    elif len(disk['Bad Partitions']) == 1:
        print_warning('  * Unable to backup this partition')
        disk['Backup Warnings'] += '{YELLOW}  * Unable to backup this partition{CLEAR}\n'.format(**COLORS)
    
    # Set description for partitions that would be clobbered
    if len(disk['Clobber Risk']) > 1:
        disk['Backup Warnings'] += '{BLUE}  + These partitions already have backup images on {Name}{CLEAR}\n'.format(**dest, **COLORS)
    elif len(disk['Clobber Risk']) == 1:
        disk['Backup Warnings'] += '{BLUE}  + This partition already has a backup image on {Name}{CLEAR}\n'.format(**dest, **COLORS)
    
    # Set warning for skipped partitions
    if len(disk['Clobber Risk']) + len(disk['Bad Partitions']) > 1:
        disk['Backup Warnings'] += '\n{YELLOW}If you continue the partitions marked above will NOT be backed up.{CLEAR}\n'.format(**COLORS)
    if len(disk['Clobber Risk']) + len(disk['Bad Partitions']) == 1:
        disk['Backup Warnings'] += '\n{YELLOW}If you continue the partition marked above will NOT be backed up.{CLEAR}\n'.format(**COLORS)

def prep_disk_for_formatting(disk=None):
    disk['Format Warnings'] = '\n'
    width = len(str(len(disk['Partitions'])))
    
    # Bail early
    if disk is None:
        raise Exception('Disk not provided.')

    # Set boot method and partition table type
    disk['Use GPT'] = True
    if (get_boot_mode() == 'UEFI'):
        if (not ask("Setup Windows to use UEFI booting?")):
            disk['Use GPT'] = False
    else:
        if (ask("Setup Windows to use BIOS/Legacy booting?")):
            disk['Use GPT'] = False
    
    # Set Display and Warning Strings
    if len(disk['Partitions']) == 0:
        disk['Format Warnings'] += 'No partitions found\n'
    for par in disk['Partitions']:
        if 'Letter' not in par or re.search(r'(RAW|Unknown)', par['FileSystem'], re.IGNORECASE):
            # FileSystem not accessible to WinPE. List partition type / OS info for technician
            par['Display String'] = '    Partition {Number:>{width}}:\t{Size} {FileSystem}\t\t{q}{Name}{q}\t{Description} ({OS})'.format(
                width=width,
                q='"' if par['Name'] != '' else '',
                **par)
        else:
            # FileSystem accessible to WinPE. List space used instead of partition type / OS info for technician
            par['Display String'] = '    Partition {Number:>{width}}:\t{Size} {FileSystem} (Used: {Used Space})\t{q}{Name}{q}'.format(
                width=width,
                q='"' if par['Name'] != '' else '',
                **par)

def print_error(message='Generic error', **kwargs):
    print('{RED}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))

def print_info(message='Generic info', **kwargs):
    print('{BLUE}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))

def print_success(message='Generic success', **kwargs):
    print('{GREEN}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))

def print_warning(message='Generic warning', **kwargs):
    print('{YELLOW}{message}{CLEAR}'.format(message=message, **COLORS, **kwargs))

def remove_volume_letters(keep=''):
    if keep is None:
        keep = ''
    try:
        # Run script
        with open(diskpart_script, 'w') as script:
            for vol in get_volumes():
                if vol['Letter'].upper() != keep.upper():
                    script.write('select volume {Number}\n'.format(**vol))
                    script.write('remove noerr\n')
        run_program('diskpart /s {script}'.format(script=diskpart_script))
    except subprocess.CalledProcessError:
        pass

def run_program(cmd=None, args=[], check=True):
    if cmd is None:
        raise Exception('No program passed.')

    if len(args) > 0:
        args = [cmd] + args
        process_return = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)
    else:
        process_return = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

    return process_return

def select_destination():
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
    """Select a disk from the attached disks"""
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
                if 'Letter' not in par or re.search(r'(RAW|Unknown)', par['FileSystem'], re.IGNORECASE):
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
        abort_to_main_menu()

def select_minidump_path():
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
    actions = [{'Name': 'Main Menu', 'Letter': 'M'},]

    # Menu loop
    selection = menu_select('Which version of Windows are we installing?', WINDOWS_VERSIONS, actions)

    if selection.isnumeric():
        return WINDOWS_VERSIONS[int(selection)-1]
    elif selection == 'M':
        abort_to_main_menu()

def setup_windows(bin=None, windows_image=None, windows_version=None):
    # Bail early
    if bin is None:
        raise Exception('bin path not specified.')
    if windows_image is None:
        raise Exception('Windows image not specified.')
    if windows_version is None:
        raise Exception('Windows version not specified.')
    
    # Apply image
    cmd = '{bin}\\wimlib\\wimlib-imagex apply "{File}.{Ext}" "{Image Name}" W:\\ {Glob}'.format(bin=bin, **windows_image, **windows_version)
    run_program(cmd)

def setup_windows_re(windows_version=None, windows_letter='W', tools_letter='T'):
    # Bail early
    if windows_version is None:
        raise Exception('Windows version not specified.')
    
    _win = '{win}:\\Windows'.format(win=windows_letter)
    _winre = '{win}\\System32\\Recovery\\WinRE.wim'.format(win=_win)
    _dest = '{tools}:\\Recovery\\WindowsRE'.format(tools=tools_letter)
    
    if re.search(r'^(8|10)', windows_version['Family']):
        # Copy WinRE.wim
        os.makedirs(_dest, exist_ok=True)
        shutil.copy(_winre, '{dest}\\WinRE.wim'.format(dest=_dest))
        
        # Set location
        run_program('{win}\\System32\\reagentc /setreimage /path {dest} /target {win}'.format(dest=_dest, win=_win))
    else:
        # Only supported on Windows 8 and above
        raise SetupError

def update_boot_partition(system_letter='S', windows_letter='W', mode='ALL'):
    run_program('bcdboot {win}:\\Windows /s {sys}: /f {mode}'.format(win=windows_letter, sys=system_letter, mode=mode))

def verify_wim_backup(bin=None, par=None):
    # Bail early
    if bin is None:
        raise Exception('bin path not specified.')
    if par is None:
        raise Exception('Partition not specified.')
    
    # Verify hiding all output for quicker verification
    print('    Partition {Number} Image...\t\t'.format(**par), end='', flush=True)
    cmd = '{bin}\\wimlib\\wimlib-imagex verify "{Image Path}\\{Image File}" --nocheck'.format(bin=bin, **par)
    if not os.path.exists('{Image Path}\\{Image File}'.format(**par)):
        print_error('Missing.')
    else:
        try:
            run_program(cmd)
            print_success('OK.')
        except subprocess.CalledProcessError as err:
            print_error('Damaged.')
            par['Error'] = par.get('Error', []) + err.stderr.decode().splitlines()
            raise BackupError

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
