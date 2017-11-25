# WK WinPE Menu

# Init
import os
import re
import subprocess
import sys
import time
import traceback
os.chdir(os.path.dirname(os.path.realpath(__file__)))
bin = os.path.abspath('..\\')
sys.path.append(os.getcwd())
from functions import *

## Colors
COLORS = {
    'CLEAR': '\033[0m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m'}

def menu_backup_imaging():
    """Take backup images of partition(s) in the WIM format and save them to a backup share"""
    errors = False

    # Set ticket ID
    os.system('cls')
    ticket_id = get_ticket_id()

    # Mount backup shares
    mount_backup_shares()

    # Select destination
    dest = select_destination()
    if dest is None:
        abort_to_main_menu('Aborting Backup Creation')

    # Select disk to backup
    disk = select_disk('For which drive are we creating backups?')
    if disk is None:
        abort_to_main_menu()
    prep_disk_for_backup(dest, disk, ticket_id)

    # Display details for backup task
    os.system('cls')
    print('Create Backup - Details:\n')
    print('    Ticket:     \t{ticket_id}'.format(ticket_id=ticket_id))
    print('    Source:     \t[{Table}] ({Type}) {Name} {Size}\n'.format(**disk))
    print('    Destination:\t{name}'.format(name=dest.get('Display Name', dest['Name'])))
    for par in disk['Partitions']:
        print(par['Display String'])
    print(disk['Backup Warnings'])

    # Ask to proceed
    if (not ask('Proceed with backup?')):
        abort_to_main_menu('Aborting Backup Creation')
    
    # Backup partition(s)
    print('\n\nStarting task.\n')
    for par in disk['Partitions']:
        try:
            backup_partition(bin, disk, par)
        except BackupError:
            errors = True
    
    # Verify backup(s)
    if disk['Valid Partitions'] > 1:
        print('\n\n  Verifying backups\n')
    else:
        print('\n\n  Verifying backup\n')
    for par in disk['Partitions']:
        if par['Number'] in disk['Bad Partitions']:
            continue # Skip verification
        try:
            verify_wim_backup(bin, par)
        except BackupError:
            errors = True

    # Print summary
    if errors:
        print_warning('\nErrors were encountered and are detailed below.')
        for par in [p for p in disk['Partitions'] if 'Error' in p]:
            print('    Partition {Number} Error:'.format(**par))
            for line in [line.strip() for line in par['Error'] if line.strip() != '']:
                print_error('\t{line}'.format(line=line))
        time.sleep(30)
    else:
        print_success('\nNo errors were encountered during imaging.')
        time.sleep(5)
    pause('\nPress Enter to return to main menu... ')

def menu_windows_setup():
    """Format a drive, partition for MBR or GPT, apply a Windows image, and rebuild the boot files"""
    errors = False

    # Set ticket ID
    os.system('cls')
    ticket_id = get_ticket_id()

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
    print('    Ticket:     \t{ticket_id}'.format(ticket_id=ticket_id))
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
    tools = [
        {'Name': 'Blue Screen View', 'Folder': 'BlueScreenView', 'File': 'BlueScreenView.exe'},
        {'Name': 'CPU-Z', 'Folder': 'CPU-Z', 'File': 'cpuz.exe'},
        {'Name': 'Fast Copy', 'Folder': 'FastCopy', 'File': 'FastCopy.exe', 'Args': ['/log', '/logfile=X:\WK\Info\FastCopy.log', '/cmd=noexist_only', '/utf8', '/skip_empty_dir', '/linkdest', '/open_window', '/balloon=FALSE', r'/exclude=$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']},
        {'Name': 'HWiNFO', 'Folder': 'HWiNFO', 'File': 'HWiNFO.exe'},
        {'Name': 'NT Password Editor', 'Folder': 'NT Password Editor', 'File': 'ntpwedit.exe'},
        {'Name': 'Notepad++', 'Folder': 'NotepadPlusPlus', 'File': 'notepadplusplus.exe'},
        {'Name': 'PhotoRec', 'Folder': 'TestDisk', 'File': 'photorec_win.exe', 'Args': ['-new_console:n']},
        {'Name': 'Prime95', 'Folder': 'Prime95', 'File': 'prime95.exe'},
        {'Name': 'ProduKey', 'Folder': 'ProduKey', 'File': 'ProduKey.exe', 'Args': ['/external', '/ExtractEdition:1']},
        {'Name': 'Q-Dir', 'Folder': 'Q-Dir', 'File': 'Q-Dir.exe'},
        {'Name': 'TestDisk', 'Folder': 'TestDisk', 'File': 'testdisk_win.exe', 'Args': ['-new_console:n']},
        ]
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Menu loop
    while True:
        selection = menu_select('Tools Menu', tools, actions)

        if (selection.isnumeric()):
            tool = tools[int(selection)-1]
            cmd = ['{bin}\\{folder}\\{file}'.format(bin=bin, folder=tool['Folder'], file=tool['File'])]
            if tool['Name'] == 'Blue Screen View':
                # Select path to scan
                minidump_path = select_minidump_path()
                if minidump_path is not None:
                    tool['Args'] = ['/MiniDumpFolder', minidump_path]
            if 'Args' in tool:
                cmd += tool['Args']
            try:
                subprocess.Popen(cmd)
            except:
                print_error('Failed to run {prog}'.format(prog=tool['Name']))
            time.sleep(2)
        elif (selection == 'M'):
            break

def menu_main():
    menus = [
        {'Name': 'Create Backups', 'Menu': menu_backup_imaging},
        {'Name': 'Setup Windows', 'Menu': menu_windows_setup},
        {'Name': 'Misc Tools', 'Menu': menu_tools},
        ]
    actions = [
        {'Name': 'Command Prompt', 'Letter': 'C'},
        {'Name': 'Reboot', 'Letter': 'R'},
        {'Name': 'Shutdown', 'Letter': 'S'},
        ]

    # Main loop
    while True:
        selection = menu_select('Main Menu', menus, actions, secret_exit=True)

        if (selection.isnumeric()):
            try:
                menus[int(selection)-1]['Menu']()
            except AbortError:
                pass
            except:
                print_error('Major exception in: {menu}'.format(menu=menus[int(selection)-1]['Name']))
                print_warning('  Please let The Wizard know and he\'ll look into it (Please include the details below).')
                print(traceback.print_exc())
                time.sleep(5)
                print_info('  You can retry but if this crashes again an alternative approach may be required.')
                pause('\nPress enter to return to the main menu')
        elif (selection == 'C'):
            run_program(['cmd', '-new_console:n'], check=False)
        elif (selection == 'R'):
            run_program(['wpeutil', 'reboot'])
        elif (selection == 'S'):
            run_program(['wpeutil', 'shutdown'])
        else:
            sys.exit(0)

if __name__ == '__main__':
    menu_main()