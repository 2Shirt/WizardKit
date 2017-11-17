# Wizard Kit: Menu

import os
import re
import subprocess
import time
import traceback
import winreg

from functions import *

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
bin = os.path.abspath('..\\')
## Check bootup type
BOOT_TYPE = 'Legacy'
try:
    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'System\\CurrentControlSet\\Control')
    reg_value = winreg.QueryValueEx(reg_key, 'PEFirmwareType')[0]
    if reg_value == 2:
        BOOT_TYPE = 'UEFI'
except:
    BOOT_TYPE = 'Unknown'

class AbortException(Exception):
    pass

def abort_to_main_menu(message='Returning to main menu...'):
    print_warning(message)
    pause('Press Enter to return to main menu... ')
    raise AbortException

def menu_backup_imaging():
    """Take backup images of partition(s) in the WIM format and save them to a backup share"""

    # Mount backup shares
    os.system('cls')
    mount_backup_shares()

    # Set ticket number
    ticket = None
    while ticket is None:
        tmp = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([-_]?\w+|))$', tmp):
            ticket = tmp

    # Select disk to backup
    disk = select_disk('For which drive are we creating backups?')
    if disk is None:
        abort_to_main_menu()

    # Get list of partitions that can't be imaged
    bad_parts = [p['Number'] for p in disk['Partitions'] if 'Letter' not in p or re.search(r'(RAW|Unknown)', p['FileSystem'])]

    # Bail if no partitions are found (that can be imaged)
    num_parts = len(disk['Partitions'])
    if num_parts == 0 or num_parts == len(bad_parts):
        abort_to_main_menu('  No partitions can be imaged for the selected drive')

    # Select destination
    dest = select_destination()
    if dest is None:
        abort_to_main_menu('Aborting Backup Creation')

    # List (and update) partition details for selected drive
    os.system('cls')
    print('Create Backup - Details:\n')
    print('    Drive:   {Size}\t[{Table}] ({Type}) {Name}\n'.format(**disk))
    clobber_risk = 0
    width=len(str(len(disk['Partitions'])))
    for par in disk['Partitions']:
        # Detail each partition
        if par['Number'] in bad_parts:
            print_warning('  * Partition {Number:>{width}}:\t{Size} {FileSystem}\t\t{q}{Name}{q}\t{Description} ({OS})'.format(
                width=width,
                q='"' if par['Name'] != '' else '',
                **par))
        else:
            # Update info for WIM capture
            par['ImageName'] = str(par['Name'])
            if par['ImageName'] == '':
                par['ImageName'] = 'Unknown'
            if 'IP' in dest:
                par['ImagePath'] = '\\\\{IP}\\{Share}\\{ticket}'.format(ticket=ticket, **dest)
            else:
                par['ImagePath'] = '{Letter}:\\{ticket}'.format(ticket=ticket, **dest)
            par['ImageFile'] = '{Number}_{ImageName}'.format(**par)
            par['ImageFile'] = '{fixed_name}.wim'.format(fixed_name=re.sub(r'\W', '_', par['ImageFile']))

            # Check for existing backups
            par['ImageExists'] = False
            if os.path.exists('{ImagePath}\\{ImageFile}'.format(**par)):
                par['ImageExists'] = True
                clobber_risk += 1
                print_info('  + Partition {Number:>{width}}:\t{Size} {FileSystem} (Used: {Used Space})\t{q}{Name}{q}'.format(
                    width=width,
                    q='"' if par['Name'] != '' else '',
                    **par))
            else:
                print('    Partition {Number:>{width}}:\t{Size} {FileSystem} (Used: {Used Space})\t{q}{Name}{q}'.format(
                    width=width,
                    q='"' if par['Name'] != '' else '',
                    **par))
    print('') # Spacer

    # Add warning about partition(s) that will be skipped
    if len(bad_parts) > 1:
        print_warning('  * Unable to backup these partitions')
    elif len(bad_parts) == 1:
        print_warning('  * Unable to backup this partition')
    if clobber_risk > 1:
        print_info('  + These partitions already have backup images on {Display Name}:'.format(**dest))
    elif clobber_risk == 1:
        print_info('  + This partition already has a backup image on {Display Name}:'.format(**dest))
    if clobber_risk + len(bad_parts) > 1:
        print_warning('\nIf you continue the partitions marked above will NOT be backed up.\n')
    if clobber_risk + len(bad_parts) == 1:
        print_warning('\nIf you continue the partition marked above will NOT be backed up.\n')

    # (re)display the destination
    print('    Destination:\t{name}\n'.format(name=dest.get('Display Name', dest['Name'])))

    # Ask to proceed
    if (not ask('Proceed with backup?')):
        abort_to_main_menu('Aborting Backup Creation')

    # Backup partition(s)
    print('\n\nStarting task.\n')
    errors = False
    for par in disk['Partitions']:
        print('    Partition {Number} Backup...\t\t'.format(**par), end='', flush=True)
        if par['Number'] in bad_parts:
            print_warning('Skipped.')
        else:
            cmd = '{bin}\\wimlib\\wimlib-imagex capture {Letter}:\\ "{ImagePath}\\{ImageFile}" "{ImageName}" "{ImageName}" --compress=fast'.format(bin=bin, **par)
            if par['ImageExists']:
                print_warning('Skipped.')
            else:
                try:
                    os.makedirs('{ImagePath}'.format(**par), exist_ok=True)
                    run_program(cmd)
                    print_success('Complete.')
                except subprocess.CalledProcessError as err:
                    print_error('Failed.')
                    errors = True
                    par['Error'] = err.stderr.decode().splitlines()

    # Verify backup(s)
    if len(par) - len(bad_parts) > 1:
        print('\n\n  Verifying backups\n')
    else:
        print('\n\n  Verifying backup\n')
    for par in disk['Partitions']:
        if par['Number'] not in bad_parts:
            print('    Partition {Number} Image...\t\t'.format(**par), end='', flush=True)
            cmd = '{bin}\\wimlib\\wimlib-imagex verify "{ImagePath}\\{ImageFile}" --nocheck'.format(bin=bin, **par)
            if not os.path.exists('{ImagePath}\\{ImageFile}'.format(**par)):
                print_error('Missing.')
            else:
                try:
                    run_program(cmd)
                    print_success('OK.')
                except subprocess.CalledProcessError as err:
                    print_error('Damaged.')
                    errors = True
                    par['Error'] = par.get('Error', []) + err.stderr.decode().splitlines()

    # Print summary
    if errors:
        print_warning('\nErrors were encountered and are detailed below.')
        for par in [p for p in disk['Partitions'] if 'Error' in p]:
            print('    Partition {Number} Error:'.format(**par))
            for line in par['Error']:
                line = line.strip()
                if line != '':
                    print_error('\t{line}'.format(line=line))
        time.sleep(300)
    else:
        print_success('\nNo errors were encountered during imaging.')
        time.sleep(10)
    pause('\nPress Enter to return to main menu... ')

def menu_windows_setup():
    """Format a drive, partition for MBR or GPT, apply a Windows image, and rebuild the boot files"""

    # Select the version of Windows to apply
    os.system('cls')
    selected_windows_version = select_windows_version()
    if selected_windows_version is None:
        abort_to_main_menu('Aborting Windows setup')

    # Find Windows image
    image = find_windows_image(selected_windows_version['ImageFile'])
    if not any(image):
        print_error('Failed to find Windows source image for {winver}'.format(winver=selected_windows_version['Name']))
        abort_to_main_menu('Aborting Windows setup')

    # Select drive to use as the OS drive
    dest_drive = select_disk('To which drive are we installing Windows?')
    if dest_drive is None:
        abort_to_main_menu('Aborting Windows setup')

    # Confirm drive format
    print_warning('All data will be deleted from the following drive:')
    print_warning('\t{Size}\t({Table}) {Name}'.format(**dest_drive))
    if (not ask('Is this correct?')):
        abort_to_main_menu('Aborting Windows setup')

    # MBR/Legacy or GPT/UEFI?
    use_gpt = True
    if (BOOT_TYPE == 'UEFI'):
        if (not ask("Setup drive using GPT (UEFI) layout?")):
            use_gpt = False
    else:
        if (ask("Setup drive using MBR (legacy) layout?")):
            use_gpt = False

    # Safety check
    print_warning('SAFETY CHECK\n')
    print_error('  FORMATTING:\tDrive: {Size}\t[{Table}] ({Type}) {Name}'.format(**dest_drive))
    if len(dest_drive['Partitions']) > 0:
        width=len(str(len(dest_drive['Partitions'])))
        for par in dest_drive['Partitions']:
            if 'Letter' not in par or re.search(r'(RAW)', par['FileSystem']):
                print_error('\t\tPartition {Number:>{width}}:\t{Size} {q}{Name}{q} ({FileSystem})\t\t{Description} ({OS})'.format(
                    width=width,
                    q='"' if par['Name'] != '' else '',
                    **par))
            else:
                print_error('\t\tPartition {Number:>{width}}:\t{Size} {q}{Name}{q} ({FileSystem})\t\t(Used space: {Used Space})'.format(
                    width=width,
                    q='"' if par['Name'] != '' else '',
                    **par))
    else:
            print_warning('\t\tNo partitions found')
    if (use_gpt):
        print('  Using:     \tGPT (UEFI) layout')
    else:
        print('  Using:     \tMBR (legacy) layout')
    print_info('  Installing:\t{winver}'.format(winver=selected_windows_version['Name']))
    if (not ask('\nIs this correct?')):
        abort_to_main_menu('Aborting Windows setup')

    # Release currently used volume letters (ensures that the drives will get S, T, & W as needed below)
    remove_volume_letters(keep=image['Source'])

    # Format and partition drive
    if (use_gpt):
        format_gpt(dest_drive, selected_windows_version['Family'])
    else:
        format_mbr(dest_drive)

    # Apply Windows image
    errors = False
    print('  Applying image...')
    cmd = '{bin}\\wimlib\\wimlib-imagex apply "{File}.{Ext}" "{ImageName}" W:\\ {Glob}'.format(bin=bin, **image, **selected_windows_version)
    try:
        run_program(cmd)
    except subprocess.CalledProcessError:
        errors = True
        print_error('Failed to apply Windows image.')

    # Create boot files
    if not errors:
        print('  Creating boot files...'.format(**selected_windows_version))
        try:
            run_program('bcdboot W:\\Windows /s S: /f ALL')
        except subprocess.CalledProcessError:
            errors = True
            print_error('Failed to create boot files.')
        if re.search(r'^(8|10)', selected_windows_version['Family']):
            try:
                run_program('W:\\Windows\\System32\\reagentc /setreimage /path T:\\Recovery\\WindowsRE /target W:\\Windows')
            except subprocess.CalledProcessError:
                # errors = True # Changed to warning.
                print_warning('Failed to setup WindowsRE files.')

    # Print summary
    if errors:
        print_warning('\nErrors were encountered during setup.')
        time.sleep(300)
    else:
        print_success('\nNo errors were encountered during setup.')
        time.sleep(10)
    pause('\nPress Enter to return to main menu... ')

def menu_tools():
    tools = [
        {'Name': 'Blue Screen View', 'Folder': 'BlueScreenView', 'File': 'BlueScreenView.exe'},
        {'Name': 'CPU-Z', 'Folder': 'CPU-Z', 'File': 'cpuz.exe'},
        {'Name': 'Explorer++', 'Folder': 'Explorer++', 'File': 'Explorer++.exe'},
        {'Name': 'Fast Copy', 'Folder': 'FastCopy', 'File': 'FastCopy.exe', 'Args': ['/log', '/logfile=X:\WK\Info\FastCopy.log', '/cmd=noexist_only', '/utf8', '/skip_empty_dir', '/linkdest', '/open_window', '/balloon=FALSE', r'/exclude=$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']},
        {'Name': 'HWiNFO', 'Folder': 'HWiNFO', 'File': 'HWiNFO.exe'},
        {'Name': 'HW Monitor', 'Folder': 'HWMonitor', 'File': 'HWMonitor.exe'},
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
                print_info('  You can reboot and try again but if this crashes again an alternative approach is required.')
                time.sleep(300)
                pause('Press Enter to shutdown...')
                run_program(['wpeutil', 'shutdown'])
        elif (selection == 'C'):
            run_program(['cmd', '-new_console:n'], check=False)
        elif (selection == 'R'):
            run_program(['wpeutil', 'reboot'])
        elif (selection == 'S'):
            run_program(['wpeutil', 'shutdown'])
        else:
            quit()

if __name__ == '__main__':
    menu_main()