# Wizard Kit PE: Functions - Backup

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

def select_backup_destination():
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
