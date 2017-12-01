# Wizard Kit PE: Functions - Backup

from functions.common import *

def backup_partition(disk, partition):
    if par['Image Exists'] or par['Number'] in disk['Bad Partitions']:
        raise GenericAbort
    
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'capture'
        '{}:\\'.format(par['Letter']),
        r'{}\{}'.format(par['Image Path'], par['Image File']),
        par['Image Name'], # Image name
        par['Image Name'], # Image description
        ' --compress=none',
        ]
    os.makedirs(par['Image Path'], exist_ok=True)
    run_program(cmd)

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
