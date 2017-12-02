# Wizard Kit PE: Functions - Backup

from functions.disk import *

# Regex
REGEX_BAD_PATH_NAMES = re.compile(
    r'([<>:"/\|\?\*]'
    r'|^(CON|PRN|AUX|NUL|COM\d*|LPT\d*)$)'
    r'|^\s+'
    r'|[\s\.]+$',
    re.IGNORECASE)

def backup_partition(disk, par):
    if par.get('Image Exists', False) or par['Number'] in disk['Bad Partitions']:
        raise GenericAbort
    
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'capture'
        '{}:\\'.format(par['Letter']),
        par['Image Path'],
        par['Image Name'], # Image name
        par['Image Name'], # Image description
        ' --compress=none',
        ]
    dest_dir = re.sub(r'(.*)\\.*$', r'\1', par['Image Path'], re.IGNORECASE)
    os.makedirs(dest_dir, exist_ok=True)
    run_program(cmd)

def fix_path(path):
    return REGEX_BAD_PATH_NAMES.sub('_', path)

def prep_disk_for_backup(destination, disk, ticket_number):
    disk['Clobber Risk'] = []
    width = len(str(len(disk['Partitions'])))

    # Get partition totals
    disk['Bad Partitions'] = [par['Number'] for par in disk['Partitions']
        if is_bad_partition(par)]
    num_valid_partitions = len(disk['Partitions']) - len(disk['Bad Partitions'])
    disk['Valid Partitions'] = num_valid_partitions
    if disk['Valid Partitions'] <= 0:
        print_error('ERROR: No partitions can be backed up for this disk')
        raise GenericAbort
    
    # Prep partitions
    for par in disk['Partitions']:
        display = '{size} {fs}'.format(
            num = par['Number'],
            width = width,
            size = par['Size'],
            fs = par['FileSystem'])
        
        if par['Number'] in disk['Bad Partitions']:
            # Set display string using partition description & OS type
            display = '* {display}\t\t{q}{name}{q}\t{desc} ({os})'.format(
                display = display,
                q = '"' if par['Name'] != '' else '',
                name = par['Name'],
                desc = par['Description'],
                os = par['OS'])
        else:
            # Update info for WIM capturing
            par['Image Name'] = par['Name'] if par['Name'] else 'Unknown'
            if 'IP' in destination:
                par['Image Path'] = r'\\{}\{}\{}'.format(
                    destination['IP'], destination['Share'], ticket_number)
            else:
                par['Image Path'] = r'{}:\{}'.format(
                    ticket_number, destination['Letter'])
            par['Image Path'] += r'\{}_{}.wim'.format(
                par['Number'], par['Image Name'])
            par['Image Path'] = fix_path(par['Image Path'])

            # Check for existing backups
            par['Image Exists'] = os.path.exists(par['Image Path'])
            if par['Image Exists']:
                disk['Clobber Risk'].append(par['Number'])
                display = '+ {}'.format(display)
            else:
                display = '  {}'.format(display)
            
            # Append rest of Display String for valid/clobber partitions
            display += ' (Used: {used})\t{q}{name}{q}'.format(
                used = par['Used Space'],
                q = '"' if par['Name'] != '' else '',
                name = par['Name'])
        # For all partitions
        par['Display String'] = display
    
    # Set description for bad partitions
    warnings = '\n'
    if disk['Bad Partitions']:
        warnings += '{}  * Unsupported filesystem{}\n'.format(
            COLORS['YELLOW'], COLORS['CLEAR'])
    if disk['Clobber Risk']:
        warnings += '{}  + Backup exists on {}{}\n'.format(
            COLORS['BLUE'], destination['Name'], COLORS['CLEAR'])
    if disk['Bad Partitions'] or disk['Clobber Risk']:
        warnings += '\n{}Marked partition(s) will NOT be backed up.{}\n'.format(
            COLORS['YELLOW'], COLORS['CLEAR'])
    disk['Backup Warnings'] = warnings

def select_backup_destination(auto_select=True):
    # Build menu
    destinations = [s for s in BACKUP_SERVERS if s['Mounted']]
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Size check
    for dest in destinations:
        if 'IP' in dest:
            dest['Usage'] = shutil.disk_usage(r'\\{IP}\{Share}'.format(**dest))
        else:
            dest['Usage'] = shutil.disk_usage('{}:\\'.format(dest['Letter']))
        dest['Free Space'] = human_readable_size(dest['Usage'].free)
        dest['Display Name'] = '{Name} ({Free Space} available)'.format(**dest)

    # Bail
    if not destinations:
        print_warning('No backup destinations found.')
        raise GenericAbort
    
    # Skip menu?
    if len(destinations) == 1 and auto_select:
        return destinations[0]
    
    selection = menu_select(
        title = 'Where are we backing up to?',
        main_entries = destinations,
        action_entries = actions)
    if selection == 'M':
        raise GenericAbort
    else:
        return destinations[int(selection)-1]

def verify_wim_backup(partition):
    if not os.path.exists(partition['Image Path']):
        raise PathNotFoundError
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'verify',
        partition['Image Path'],
        ' --nocheck',
        ]
    run_program(cmd)

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
