# Wizard Kit PE: Menus

from functions.backup import *
from functions.disk import *
from functions.windows_setup import *

# STATIC VARIABLES
FAST_COPY_ARGS = [
    '/cmd=noexist_only',
    '/utf8',
    '/skip_empty_dir',
    '/linkdest',
    '/no_ui',
    '/auto_close',
    '/exclude={}'.format(';'.join(FAST_COPY_EXCLUDES)),
    ]
PE_TOOLS = {
    'BlueScreenView': {
        'Path': r'BlueScreenView\BlueScreenView.exe',
        },
    'FastCopy': {
        'Path': r'FastCopy\FastCopy.exe',
        'Args': FAST_COPY_ARGS,
        },
    'HWiNFO': {
        'Path': r'HWiNFO\HWiNFO.exe',
        },
    'NT Password Editor': {
        'Path': r'NT Password Editor\ntpwedit.exe',
        },
    'Notepad++': {
        'Path': r'NotepadPlusPlus\NotepadPlusPlus.exe',
        },
    'PhotoRec': {
        'Path': r'TestDisk\photorec_win.exe',
        'Args': ['-new_console:n'],
        },
    'Prime95': {
        'Path': r'Prime95\prime95.exe',
        },
    'ProduKey': {
        'Path': r'ProduKey\ProduKey.exe',
        },
    'Q-Dir': {
        'Path': r'Q-Dir\Q-Dir.exe',
        },
    'TestDisk': {
        'Path': r'TestDisk\testdisk_win.exe',
        'Args': ['-new_console:n'],
        },
    }

def menu_backup():
    """Take backup images of partition(s) in the WIM format and save them to a backup share"""
    errors = False
    other_results = {
        'Error': {
            'CalledProcessError':   'Unknown Error',
            'PathNotFoundError':    'Missing',
        },
        'Warning': {
            'GenericAbort':         'Skipped',
            'GenericRepair':        'Repaired',
        }}
    set_title('{}: Backup Menu'.format(KIT_NAME_FULL))

    # Set ticket Number
    os.system('cls')
    ticket_number = get_ticket_number()

    # Mount backup shares
    mount_backup_shares()

    # Select destination
    destination = select_backup_destination()

    # Select disk to backup
    disk = select_disk('For which drive are we creating backups?')
    if not disk:
        raise GenericAbort
    
    # "Prep" disk?
    prep_disk_for_backup(destination, disk, ticket_number)

    # Display details for backup task
    os.system('cls')
    print_info('Create Backup - Details:\n')
    # def show_info(message='~Some message~', info='~Some info~', indent=8, width=32):
    show_info(message='Ticket:', info=ticket_number)
    show_info(
        message = 'Source:',
        info = '[{Table}] ({Type}) {Name} {Size}'.format(**disk),
        )
    show_info(
        message = 'Destination:',
        info = destination.get('Display Name', destination['Name']),
        )
    for par in disk['Partitions']:
        show_info(message='', info=par['Display String'], width=20)
    print_standard(disk['Backup Warnings'])

    # Ask to proceed
    if (not ask('Proceed with backup?')):
        raise GenericAbort
    
    # Backup partition(s)
    print_info('\n\nStarting task.\n')
    for par in disk['Partitions']:
        message = 'Partition {} Backup...'.format(par['Number'])
        result = try_and_print(message=message, function=backup_partition,
            other_results=other_results, disk=disk, partition=par)
        if not result['CS']:
            errors = True
            par['Error'] = result['Error']
    
    # Verify backup(s)
    if disk['Valid Partitions']:
        print_info('\n\n  Verifying backup images(s)\n')
        for par in disk['Partitions']:
            if par['Number'] in disk['Bad Partitions']:
                continue # Skip verification
            message = 'Partition {} Image...'.format(par['Number'])
            result = try_and_print(message=message, function=verify_wim_backup,
                other_results=other_results, partition=par)
            if not result['CS']:
                errors = True
                par['Error'] = result['Error']

    # Print summary
    if errors:
        print_warning('\nErrors were encountered and are detailed below.')
        for par in [p for p in disk['Partitions'] if 'Error' in p]:
            print_standard('    Partition {} Error:'.format(par['Number']))
            if hasattr(par['Error'], 'stderr'):
                try:
                    par['Error'] = par['Error'].stderr.decode()
                except:
                    # Deal with badly formatted error message
                    pass
            if isinstance(par['Error'], basestring):
                print_error('\t{}'.format(par['Error']))
            else:
                try:
                    par['Error'] = par['Error'].splitlines()
                    par['Error'] = [line.strip() for line in par['Error']]
                    par['Error'] = [line for line in par['Error'] if line]
                except:
                    pass
                for line in par['Error']:
                    print_error('\t{}'.format(line))
        time.sleep(30)
    else:
        print_success('\nNo errors were encountered during imaging.')
        time.sleep(5)
    pause('\nPress Enter to return to main menu... ')

def menu_root():
    menus = [
        {'Name': 'Create Backups', 'Menu': menu_backup},
        {'Name': 'Setup Windows', 'Menu': menu_setup},
        {'Name': 'Misc Tools', 'Menu': menu_tools},
        ]
    actions = [
        {'Name': 'Command Prompt', 'Letter': 'C'},
        {'Name': 'Reboot', 'Letter': 'R'},
        {'Name': 'Shutdown', 'Letter': 'S'},
        ]

    # Main loop
    while True:
        set_title(KIT_NAME_FULL)
        selection = menu_select(
            title = 'Main Menu',
            main_entries = menus,
            action_entries = actions,
            secret_exit = True)

        if (selection.isnumeric()):
            try:
                menus[int(selection)-1]['Menu']()
            except AbortError:
                pass
        elif (selection == 'C'):
            run_program(['cmd', '-new_console:n'], check=False)
        elif (selection == 'R'):
            run_program(['wpeutil', 'reboot'])
        elif (selection == 'S'):
            run_program(['wpeutil', 'shutdown'])
        else:
            exit_script()

def menu_setup():
    """Format a drive, partition for MBR or GPT, apply a Windows image, and rebuild the boot files"""
    errors = False
    set_title('{}: Setup Menu'.format(KIT_NAME_FULL))

    # Set ticket ID
    os.system('cls')
    ticket_number = get_ticket_number()

    # Select the version of Windows to apply
    windows_version = select_windows_version()

    # Select drive to use as the OS drive
    dest_disk = select_disk('To which drive are we installing Windows?')
    prep_disk_for_formatting(dest_disk)
    
    # Find Windows image
    ## NOTE: Needs to happen AFTER select_disk() is called as there's a hidden assign_volume_letters().
    ##       This changes the current letters thus preventing installing from a local source.
    windows_image = find_windows_image(bin, windows_version)

    # Display details for setup task
    os.system('cls')
    print('Setup Windows - Details:\n')
    print('    Ticket:     \t{ticket_number}'.format(ticket_number=ticket_number))
    print('    Installing: \t{winver}'.format(winver=windows_version['Name']))
    print('    Boot Method:\t{_type}'.format(
        _type='UEFI (GPT)' if dest_disk['Use GPT'] else 'Legacy (MBR)'))
    print('    Using Image:\t{File}.{Ext}'.format(**windows_image))
    print_warning('    ERASING:    \t[{Table}] ({Type}) {Name} {Size}\n'.format(**dest_disk))
    for par in dest_disk['Partitions']:
        print_warning(par['Display String'])
    print_warning(dest_disk['Format Warnings'])
    
    if (not ask('Is this correct?')):
        abort_to_main_menu('Aborting Windows setup')
    
    # Safety check    
    print('\nSAFETY CHECK')
    print_warning('All data will be DELETED from the drive and partition(s) listed above.')
    print_warning('This is irreversible and will lead to {CLEAR}{RED}DATA LOSS.'.format(**COLORS))
    if (not ask('Asking again to confirm, is this correct?')):
        abort_to_main_menu('Aborting Windows setup')

    # Release currently used volume letters (ensures that the drives will get S, T, & W as needed below)
    remove_volume_letters(keep=windows_image['Source'])

    # Format and partition drive
    print('\n    Formatting Drive...     \t\t', end='', flush=True)
    try:
        if (dest_disk['Use GPT']):
            format_gpt(dest_disk, windows_version['Family'])
        else:
            format_mbr(dest_disk, windows_version['Family'])
        print_success('Complete.')
    except:
        # We need to crash as the drive is in an unknown state
        print_error('Failed.')
        raise

    # Apply Image
    print('    Applying Image...       \t\t', end='', flush=True)
    try:
        setup_windows(bin, windows_image, windows_version)
        print_success('Complete.')
    except subprocess.CalledProcessError:
        print_error('Failed.')
        errors = True
    except:
        # We need to crash as the OS is in an unknown state
        print_error('Failed.')
        raise
    
    # Create Boot files
    print('    Update Boot Partition...\t\t', end='', flush=True)
    try:
        update_boot_partition()
        print_success('Complete.')
    except subprocess.CalledProcessError:
        # Don't need to crash as this is (potentially) recoverable
        print_error('Failed.')
        errors = True
    except:
        print_error('Failed.')
        raise
    
    # Setup WinRE
    print('    Update Recovery Tools...\t\t', end='', flush=True)
    try:
        setup_windows_re(windows_version)
        print_success('Complete.')
    except SetupError:
        print('Skipped.')
    except:
        # Don't need to crash as this is (potentially) recoverable
        print_error('Failed.')
        errors = True

    # Print summary
    if errors:
        print_warning('\nErrors were encountered during setup.')
        time.sleep(30)
    else:
        print_success('\nNo errors were encountered during setup.')
        time.sleep(5)
    pause('\nPress Enter to return to main menu... ')

def menu_tools():
    tools = [k for k in sorted(PE_TOOLS.keys())]
    actions = [{'Name': 'Main Menu', 'Letter': 'M'},]
    set_title(KIT_NAME_FULL)

    # Menu loop
    while True:
        selection = menu_select(
            title = 'Tools Menu',
            main_entries = tools,
            action_entries = actions)
        if (selection.isnumeric()):
            tool = tools[int(selection)-1]
            cmd = [PE_TOOLS[tool]['Path']] + PE_TOOLS[tool].get('Args', [])
            if tool == 'Blue Screen View':
                # Select path to scan
                minidump_path = select_minidump_path()
                if minidump_path:
                    cmd.extend(['/MiniDumpFolder', minidump_path])
            try:
                popen_program(cmd)
            except Exception:
                print_error('Failed to run {prog}'.format(prog=tool['Name']))
                time.sleep(2)
                pause()
        elif (selection == 'M'):
            break

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
    selection = menu_select(
        title = 'Which BSoD / MiniDump path are we scanning?',
        main_entries = dumps)
    return dumps[int(selection) - 1]['Name']

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
