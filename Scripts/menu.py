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

def menu_backup_imaging():
    """Take backup images of partition(s) in the WIM format and save them to a backup share"""
    errors = False

    # Mount backup shares
    os.system('cls')
    mount_backup_shares()

    # Set ticket ID
    ticket_id = get_ticket_id()

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
    print('    Drive:   {Size}\t[{Table}] ({Type}) {Name}\n'.format(**disk))
    for par in disk['Partitions']:
        print(par['Display String'])
    print(disk['Backup Warnings'])
    print('\n    Destination:\t{name}\n'.format(name=dest.get('Display Name', dest['Name'])))

    # Ask to proceed
    if (not ask('Proceed with backup?')):
        abort_to_main_menu('Aborting Backup Creation')
    
    # Backup partition(s)
    print('\n\nStarting task.\n')
    for par in disk['Partitions']:
        try:
            backup_partition(bin, par)
        except BackupException:
            errors = True
    
    # Verify backup(s)
    if len(disk['Valid Partitions']) > 1:
        print('\n\n  Verifying backups\n')
    else:
        print('\n\n  Verifying backup\n')
    for par in disk['Partitions']:
        if par['Number'] in disk['Bad Partitions']:
            continue # Skip verification
        try:
            verify_wim_backup(bin, par)
        except BackupException:
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

    # Select the version of Windows to apply
    os.system('cls')
    windows_version = select_windows_version()
    
    # Find Windows image
    windows_image = find_windows_image(bin, windows_version)

    # Select drive to use as the OS drive
    dest_disk = select_disk('To which drive are we installing Windows?')
    prep_disk_for_formatting(dest_disk)

    # Safety check
    print_warning('SAFETY CHECK\n')
    print_error(dest_disk['Format Warnings'])
    for par in dest_disk['Partitions']:
        print_error(par['Display String'])
    print_info('\n  Installing:\t{winver}'.format(winver=windows_version['Name']))
    if (not ask('\nIs this correct?')):
        abort_to_main_menu('Aborting Windows setup')

    # Release currently used volume letters (ensures that the drives will get S, T, & W as needed below)
    remove_volume_letters(keep=windows_image['Source'])

    # Format and partition drive
    if (dest_disk['Use GPT']):
        format_gpt(dest_disk, windows_version['Family'])
    else:
        format_mbr(dest_disk, windows_version['Family'])

    # Setup Windows
    try:
        setup_windows(bin, windows_image, windows_version)
        setup_boot_files(windows_version)
    except SetupException:
        errors = True

    # Print summary
    if errors:
        print_warning('\nErrors were encountered during setup.')
        time.sleep(30)
    else:
        print_success('\nDone.')
        time.sleep(5)
    pause('\nPress Enter to return to main menu... ')

def menu_tools():
    tools = [
        {'Name': 'Blue Screen View', 'Folder': 'BlueScreenView', 'File': 'BlueScreenView.exe'},
        {'Name': 'CPU-Z', 'Folder': 'CPU-Z', 'File': 'cpuz.exe'},
        {'Name': 'Fast Copy', 'Folder': 'FastCopy', 'File': 'FastCopy.exe', 'Args': ['/log', '/logfile=X:\WK\Info\FastCopy.log', '/cmd=noexist_only', '/utf8', '/skip_empty_dir', '/linkdest', '/open_window', '/balloon=FALSE', r'/exclude=$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']},
        {'Name': 'HWiNFO', 'Folder': 'HWiNFO', 'File': 'HWiNFO.exe'},
        {'Name': 'NT Password Editor', 'Folder': 'NT Password Editor', 'File': 'ntpwedit.exe'},
        {'Name': 'Notepad2', 'Folder': 'Notepad2', 'File': 'Notepad2-Mod.exe'},
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
        {'Name': 'Install Windows', 'Menu': menu_windows_setup},
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
            except AbortException:
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