# Wizard Kit: WinPE Menus

from functions.backup import *
from functions.disk import *
from functions.windows_setup import *
from settings.winpe import *


def check_pe_tools():
  """Fix tool paths for WinPE layout."""
  for k in PE_TOOLS.keys():
    PE_TOOLS[k]['Path'] = r'{}\{}'.format(
      global_vars['BinDir'], PE_TOOLS[k]['Path'])
  global_vars['Tools']['wimlib-imagex'] = re.sub(
    r'\\x(32|64)',
    r'',
    global_vars['Tools']['wimlib-imagex'],
    re.IGNORECASE)


def menu_backup():
  """Take backup images of partition(s) in the WIM format."""
  errors = False
  other_results = {
    'Error': {
      'CalledProcessError':   'Unknown Error',
      'PathNotFoundError':  'Missing',
    },
    'Warning': {
      'GenericAbort':     'Skipped',
      'GenericRepair':    'Repaired',
    }}
  set_title('{}: Backup Menu'.format(KIT_NAME_FULL))

  # Set backup prefix
  clear_screen()
  print_standard('{}\n'.format(global_vars['Title']))
  ticket_number = get_ticket_number()
  if ENABLED_TICKET_NUMBERS:
    backup_prefix = ticket_number
  else:
    backup_prefix = get_simple_string(prompt='Enter backup name prefix')
    backup_prefix = backup_prefix.replace(' ', '_')

  # Assign drive letters
  try_and_print(
    message = 'Assigning letters...',
    function = assign_volume_letters,
    other_results = other_results)

  # Mount backup shares
  mount_backup_shares(read_write=True)

  # Select destination
  destination = select_backup_destination(auto_select=False)

  # Scan disks
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
  prep_disk_for_backup(destination, disk, backup_prefix)

  # Display details for backup task
  clear_screen()
  print_info('Create Backup - Details:\n')
  if ENABLED_TICKET_NUMBERS:
    show_data(message='Ticket:', data=ticket_number)
  show_data(
    message = 'Source:',
    data = '[{}] ({}) {} {}'.format(
      disk.get('Table', ''),
      disk.get('Type', ''),
      disk.get('Name', 'Unknown'),
      disk.get('Size', ''),
      ),
    )
  show_data(
    message = 'Destination:',
    data = destination.get('Display Name', destination['Name']),
    )
  for par in disk['Partitions']:
    message = 'Partition {}:'.format(par['Number'])
    data = par['Display String']
    if par['Number'] in disk['Bad Partitions']:
      show_data(message=message, data=data, width=30, warning=True)
      if 'Error' in par:
        show_data(message='', data=par['Error'], error=True)
    elif par['Image Exists']:
      show_data(message=message, data=data, width=30, info=True)
    else:
      show_data(message=message, data=data, width=30)
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
      par = par)
    if not result['CS'] and not isinstance(result['Error'], GenericAbort):
      errors = True
      par['Error'] = result['Error']

  # Verify backup(s)
  if disk['Valid Partitions']:
    print_info('\n\nVerifying backup images(s)\n')
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
      print_standard('  Partition {} Error:'.format(par['Number']))
      if hasattr(par['Error'], 'stderr'):
        try:
          par['Error'] = par['Error'].stderr.decode()
        except:
          # Deal with badly formatted error message
          pass
      try:
        par['Error'] = par['Error'].splitlines()
        par['Error'] = [line.strip() for line in par['Error']]
        par['Error'] = [line for line in par['Error'] if line]
        for line in par['Error']:
          print_error('\t{}'.format(line))
      except:
        print_error('\t{}'.format(par['Error']))
  else:
    print_success('\nNo errors were encountered during imaging.')
  if 'LogFile' in global_vars and ask('\nReview log?'):
    cmd = [
      global_vars['Tools']['NotepadPlusPlus'],
      global_vars['LogFile']]
    try:
      popen_program(cmd)
    except Exception:
      print_error('ERROR: Failed to open log.')
      sleep(30)
  pause('\nPress Enter to return to main menu... ')


def menu_root():
  """Main WinPE menu."""
  check_pe_tools()
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
      except GenericAbort:
        print_warning('\nAborted\n')
        pause('Press Enter to return to main menu... ')
    elif (selection == 'C'):
      run_program(['cmd', '-new_console:n'], check=False)
    elif (selection == 'R'):
      run_program(['wpeutil', 'reboot'])
    elif (selection == 'S'):
      run_program(['wpeutil', 'shutdown'])
    else:
      sys.exit()


def menu_setup():
  """Format a disk, apply a Windows image, and create boot files."""
  errors = False
  other_results = {
    'Error': {
      'CalledProcessError':   'Unknown Error',
      'PathNotFoundError':  'Missing',
    },
    'Warning': {
      'GenericAbort':     'Skipped',
      'GenericRepair':    'Repaired',
    }}
  set_title('{}: Setup Menu'.format(KIT_NAME_FULL))

  # Set ticket ID
  clear_screen()
  print_standard('{}\n'.format(global_vars['Title']))
  ticket_number = get_ticket_number()

  # Select the version of Windows to apply
  windows_version = select_windows_version()

  # Find Windows image
  # NOTE: Reassign volume letters to ensure all devices are scanned
  try_and_print(
    message = 'Assigning volume letters...',
    function = assign_volume_letters,
    other_results = other_results)
  windows_image = find_windows_image(windows_version)

  # Scan disks
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
  if not dest_disk:
    raise GenericAbort

  # "Prep" disk
  prep_disk_for_formatting(dest_disk)

  # Display details for setup task
  clear_screen()
  print_info('Setup Windows - Details:\n')
  if ENABLED_TICKET_NUMBERS:
    show_data(message='Ticket:', data=ticket_number)
  show_data(message='Installing:', data=windows_version['Name'])
  show_data(
    message = 'Boot Method:',
    data = 'UEFI (GPT)' if dest_disk['Use GPT'] else 'Legacy (MBR)')
  show_data(message='Using Image:', data=windows_image['Path'])
  show_data(
    message = 'ERASING:',
    data = '[{}] ({}) {} {}\n'.format(
      dest_disk.get('Table', ''),
      dest_disk.get('Type', ''),
      dest_disk.get('Name', 'Unknown'),
      dest_disk.get('Size', ''),
      ),
    warning = True)
  for par in dest_disk['Partitions']:
    show_data(
      message = 'Partition {}:'.format(par['Number']),
      data = par['Display String'],
      warning = True)
  print_warning(dest_disk['Format Warnings'])

  if (not ask('Is this correct?')):
    raise GenericAbort

  # Safety check
  print_standard('\nSAFETY CHECK')
  print_warning('All data will be DELETED from the '
          'disk and partition(s) listed above.')
  print_warning('This is irreversible and will lead '
          'to {CLEAR}{RED}DATA LOSS.'.format(**COLORS))
  if (not ask('Asking again to confirm, is this correct?')):
    raise GenericAbort

  # Remove volume letters so S, T, & W can be used below
  try_and_print(
    message = 'Removing volume letters...',
    function = remove_volume_letters,
    other_results = other_results,
    keep=windows_image['Letter'])

  # Assign new letter for local source if necessary
  if windows_image['Local'] and windows_image['Letter'] in ['S', 'T', 'W']:
    new_letter = try_and_print(
      message = 'Reassigning source volume letter...',
      function = reassign_volume_letter,
      other_results = other_results,
      letter=windows_image['Letter'])
    windows_image['Path'] = '{}{}'.format(
      new_letter, windows_image['Path'][1:])
    windows_image['Letter'] = new_letter

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

  # Copy WinPE log(s)
  source = r'{}\Logs'.format(global_vars['ClientDir'])
  dest = r'W:\{}\Logs\WinPE'.format(KIT_NAME_SHORT)
  shutil.copytree(source, dest)

  # Print summary
  print_standard('\nDone.')
  if 'LogFile' in global_vars and ask('\nReview log?'):
    cmd = [
      global_vars['Tools']['NotepadPlusPlus'],
      global_vars['LogFile']]
    try:
      popen_program(cmd)
    except Exception:
      print_error('ERROR: Failed to open log.')
      sleep(30)
  pause('\nPress Enter to return to main menu... ')


def menu_tools():
  """Tool launcher menu."""
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
      name = tools[int(selection)-1]['Name']
      cmd = [PE_TOOLS[name]['Path']] + PE_TOOLS[name].get('Args', [])
      if name == 'Blue Screen View':
        # Select path to scan
        minidump_path = select_minidump_path()
        if minidump_path:
          cmd.extend(['/MiniDumpFolder', minidump_path])
      try:
        popen_program(cmd)
      except Exception:
        print_error('Failed to run {}'.format(name))
        sleep(2)
        pause()
    elif (selection == 'M'):
      break


def select_minidump_path():
  """Select BSOD minidump path from a menu."""
  dumps = []

  # Assign volume letters first
  assign_volume_letters()

  # Search for minidumps
  set_thread_error_mode(silent=True) # Prevents "No disk" popups
  for d in psutil.disk_partitions():
    if global_vars['Env']['SYSTEMDRIVE'].upper() in d.mountpoint:
      # Skip RAMDisk
      continue
    if os.path.exists(r'{}Windows\MiniDump'.format(d.mountpoint)):
      dumps.append({'Name': r'{}Windows\MiniDump'.format(d.mountpoint)})
  set_thread_error_mode(silent=False) # Return to normal

  # Check results before showing menu
  if len(dumps) == 0:
    print_error('ERROR: No BSoD / MiniDump paths found')
    sleep(2)
    return None

  # Menu
  selection = menu_select(
    title = 'Which BSoD / MiniDump path are we scanning?',
    main_entries = dumps)
  return dumps[int(selection) - 1]['Name']


if __name__ == '__main__':
  print("This file is not meant to be called directly.")

# vim: sts=2 sw=2 ts=2
