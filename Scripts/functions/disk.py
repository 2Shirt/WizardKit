# Wizard Kit PE: Functions - Disk

from functions.common import *
import partition_uids

def assign_volume_letters():
    try:
        # Run script
        with open(DISKPART_SCRIPT, 'w') as script:
            for vol in get_volumes():
                script.write('select volume {Number}\n'.format(**vol))
                script.write('assign\n')
        run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
    except subprocess.CalledProcessError:
        pass

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
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('detail disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
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
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('list disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
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
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('select partition {Number}\n'.format(**par))
            script.write('detail partition\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
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
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('list partition\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
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
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('select disk {Number}\n'.format(**disk))
            script.write('uniqueid disk\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
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

def get_volumes():
    vols = []
    
    try:
        # Run script
        with open(DISKPART_SCRIPT, 'w') as script:
            script.write('list volume\n')
        process_return = run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
        process_return = process_return.stdout.decode().strip()
    except subprocess.CalledProcessError:
        pass
    else:
        # Append volume numbers
        for tmp in re.findall(r'Volume (\d+)\s+([A-Za-z]?)\s+', process_return):
            vols.append({'Number': tmp[0], 'Letter': tmp[1]})
    
    return vols

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

def remove_volume_letters(keep=''):
    if keep is None:
        keep = ''
    try:
        # Run script
        with open(DISKPART_SCRIPT, 'w') as script:
            for vol in get_volumes():
                if vol['Letter'].upper() != keep.upper():
                    script.write('select volume {Number}\n'.format(**vol))
                    script.write('remove noerr\n')
        run_program('diskpart /s {script}'.format(script=DISKPART_SCRIPT))
    except subprocess.CalledProcessError:
        pass

def select_disk(title='Which disk?'):
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
    selection = menu_select(
        title = title,
        main_entries = disk_options,
        action_entries = actions)

    if (selection.isnumeric()):
        return disk_options[int(selection)-1]['Disk']
    elif (selection == 'M'):
        abort_to_main_menu()

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
