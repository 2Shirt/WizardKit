# Wizard Kit PE: Menus

from functions.backup import *
from functions.disk import *
from functions.windows_setup import *

# STATIC VARIABLES
FAST_COPY_PE_ARGS = [
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
        'Args': FAST_COPY_PE_ARGS,
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
    """Take backup images of partition(s) in the WIM format."""
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
    clear_screen()
    ticket_number = get_ticket_number()

    # Mount backup shares
    mount_backup_shares()

    # Select destination
    destination = select_backup_destination()

    # Scan disks
    try_and_print(
        message = 'Assigning letters...',
        function = assign_volume_letters,
        other_results = other_results)
    result = try_and_print(
        message = 'Getting disk info...',
        function = scan_disks,
        other_results = other_results)
    if result['CS']:
        disks = result['Out']
    else:
        print_error('ERROR: No disks found.')
        raise GenericAbort
    
    # Select disk to backup
    disk = select_disk('For which disk are we creating backups?', disks)
    if not disk:
        raise GenericAbort
    
    # "Prep" disk
    prep_disk_for_backup(destination, disk, ticket_number)

    # Display details for backup task
    clear_screen()
    print_info('Create Backup - Details:\n')
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
        result = try_and_print(
            message = 'Partition {} Backup...'.format(par['Number']),
            function = backup_partition,
            other_results = other_results,
            disk = disk,
            partition = par)
        if not result['CS']:
            errors = True
            par['Error'] = result['Error']
    
    # Verify backup(s)
    if disk['Valid Partitions']:
        print_info('\n\n  Verifying backup images(s)\n')
        for par in disk['Partitions']:
            if par['Number'] in disk['Bad Partitions']:
                continue # Skip verification
            result = try_and_print(
                message = 'Partition {} Image...'.format(par['Number']),
                function = verify_wim_backup,
                other_results = other_results,
                partition = par)
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
    """Format a disk (MBR/GPT), apply a Windows image, and setup boot files."""
    errors = False
    set_title('{}: Setup Menu'.format(KIT_NAME_FULL))

    # Set ticket ID
    clear_screen()
    ticket_number = get_ticket_number()

    # Select the version of Windows to apply
    windows_version = select_windows_version()
    
    # Find Windows image
    windows_image = find_windows_image(windows_version)

    # Scan disks
    try_and_print(
        message = 'Assigning letters...',
        function = assign_volume_letters,
        other_results = other_results)
    result = try_and_print(
        message = 'Getting disk info...',
        function = scan_disks,
        other_results = other_results)
    if result['CS']:
        disks = result['Out']
    else:
        print_error('ERROR: No disks found.')
        raise GenericAbort
    
    # Select disk to use as the OS disk
    dest_disk = select_disk('To which disk are we installing Windows?', disks)
    if not disk:
        raise GenericAbort
    
    # "Prep" disk
    prep_disk_for_formatting(dest_disk)

    # Display details for setup task
    clear_screen()
    print_info('Setup Windows - Details:\n')
    show_info(message='Ticket:', info=ticket_number)
    show_info(message='Installing:', info=windows_version['Name'])
    show_info(
        message = 'Boot Method:',
        info = 'UEFI (GPT)' if dest_disk['Use GPT'] else 'Legacy (MBR)')
    show_info(message='Using Image:', info=windows_version['Path'])
    print_warning('    ERASING:    \t[{Table}] ({Type}) {Name} {Size}\n'.format(
        **dest_disk))
    for par in dest_disk['Partitions']:
        print_warning(par['Display String'])
    print_warning(dest_disk['Format Warnings'])
    
    if (not ask('Is this correct?')):
        raise GeneralAbort
    
    # Safety check
    print_standard('\nSAFETY CHECK')
    print_warning('All data will be DELETED from the '
                  'disk & partition(s) listed above.')
    print_warning('This is irreversible and will lead '
                  'to {CLEAR}{RED}DATA LOSS.'.format(**COLORS))
    if (not ask('Asking again to confirm, is this correct?')):
        raise GeneralAbort

    # Remove volume letters so S, T, & W can be used below
    remove_volume_letters(keep=windows_image['Source'])
    new_letter = reassign_volume_letter(letter=windows_image['Source'])
    if new_letter:
        windows_image['Source'] = new_letter

    # Format and partition disk
    result = try_and_print(
        message = 'Formatting disk...',
        function = format_disk,
        other_results = other_results,
        disk = dest_disk,
        use_gpt = dest_disk['Use GPT'])
    if not result['CS']:
        # We need to crash as the disk is in an unknown state
        print_error('ERROR: Failed to format disk.')
        raise GenericAbort

    # Apply Image
    result = try_and_print(
        message = 'Applying image...',
        function = setup_windows,
        other_results = other_results,
        windows_image = windows_image,
        windows_version = windows_version)
    if not result['CS']:
        # We need to crash as the disk is in an unknown state
        print_error('ERROR: Failed to apply image.')
        raise GenericAbort
    
    # Create Boot files
    try_and_print(
        message = 'Updating boot files...',
        function = update_boot_partition,
        other_results = other_results)
    
    # Setup WinRE
    try_and_print(
        message = 'Updating recovery tools...',
        function = setup_windows_re,
        other_results = other_results,
        windows_version = windows_version)

    # Print summary
    print_standard('\nDone.')
    pause('\nPress Enter to return to main menu... ')

def menu_tools():
    tools = [{'Name': k} for k in sorted(PE_TOOLS.keys())]
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
    for disk in tmp:
        if os.path.exists('{}:\\Windows\\MiniDump'.format(disk)):
            dumps.append({'Name': '{}:\\Windows\\MiniDump'.format(disk)})

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
