# Wizard Kit: Copy user data to the system over the network

import os
import re
from operator import itemgetter

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Data 1')
from functions import *
init_global_vars()
set_global_vars(LogFile='{LogDir}\\Data 1.log'.format(**global_vars))
set_global_vars(TransferDir='{ClientDir}\\Transfer'.format(**global_vars))

def abort():
    print_warning('Aborted.')
    exit_script(global_vars)

def transfer_file_based(source_path, subdir=None):
    # Set Destination
    if subdir is None:
        dest_path = global_vars['TransferDir']
    else:
        dest_path = '{TransferDir}\\{subdir}'.format(subdir=subdir, **global_vars)
    os.makedirs(dest_path, exist_ok=True)
    
    # Main copy
    selected_items = []
    for item in os.scandir(source_path):
        if REGEX_INCL_ROOT_ITEMS.search(item.name):
            selected_items.append(item.path)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item.name):
            if ask('Copy: "{name}" item?'.format(name=item.name)):
                selected_items.append(item.path)
    if len(selected_items) > 0:
        _args = global_vars['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying main user data...')
            run_program(global_vars['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying main user data')
    else:
        print_error('ERROR: No files selected for transfer?')
        abort()

    # Fonts
    selected_items = []
    if os.path.exists('{source}\\Windows\\Fonts'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\Fonts'.format(source=source_path))
    if len(selected_items) > 0:
        _args = global_vars['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\Windows\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying Fonts...')
            run_program(global_vars['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying Fonts')

    # Registry
    selected_items = []
    if os.path.exists('{source}\\Windows\\System32\\config'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\System32\\config'.format(source=source_path))
    if os.path.exists('{source}\\Windows\\System32\\OEM'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\System32\\OEM'.format(source=source_path))
    if len(selected_items) > 0:
        _args = global_vars['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\Windows\\System32\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying Registry...')
            run_program(global_vars['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying registry')

def transfer_image_based(source_path):
    print_standard('Assessing image...')
    os.makedirs(global_vars['TransferDir'], exist_ok=True)

    # Scan source
    _args = [
        'dir',
        '{source}'.format(source=source_path), '1']
    try:
        _list = run_program(global_vars['Tools']['wimlib-imagex'], _args, check=True)
    except subprocess.CalledProcessError as err:
        print_error('ERROR: Failed to get file list.')
        print(err)
        abort()

    # Add items to list
    selected_items = []
    root_items = [i.strip() for i in _list.stdout.decode('utf-8', 'ignore').splitlines() if i.count('\\') == 1 and i.strip() != '\\']
    for item in root_items:
        if REGEX_INCL_ROOT_ITEMS.search(item):
            selected_items.append(item)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item):
            if ask('Extract: "{name}" item?'.format(name=item)):
                selected_items.append(item)

    # Extract files
    if len(selected_items) > 0:
        # Write files.txt
        with open('{TmpDir}\\wim_files.txt'.format(**global_vars), 'w') as f:
            # Defaults
            for item in EXTRA_INCL_WIM_ITEMS:
                f.write('{item}\n'.format(item=item))
            for item in selected_items:
                f.write('{item}\n'.format(item=item))
        try:
            print_standard('Extracting user data...')
            _args = [
                'extract',
                '{source}'.format(source=source_path), '1',
                '@{TmpDir}\\wim_files.txt'.format(**global_vars),
                '--dest-dir={TransferDir}\\'.format(**global_vars),
                '--no-acls',
                '--nullglob']
            run_program(global_vars['Tools']['wimlib-imagex'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while extracting user data')
    else:
        print_error('ERROR: No files selected for extraction?')
        abort()

if __name__ == '__main__':
    stay_awake(global_vars)
    # Check for existing TransferDir
    if os.path.exists(global_vars['TransferDir']):
        print_warning('Folder "{TransferDir}" exists. This script will rename the existing folder in order to avoid overwriting data.'.format(**global_vars))
        if (ask('Rename existing folder and proceed?')):
            _old_transfer = '{TransferDir}.old'.format(**global_vars)
            _i = 1;
            while os.path.exists(_old_transfer):
                _old_transfer = '{TransferDir}.old{i}'.format(i=_i, **global_vars)
                _i += 1
            print_info('Renaming "{TransferDir}" to "{old_transfer}"'.format(old_transfer=_old_transfer, **global_vars))
            os.rename(global_vars['TransferDir'], _old_transfer)
        else:
            abort()

    # Set ticket number
    ticket = None
    while ticket is None:
        tmp = input('Enter ticket number: ')
        if re.match(r'^([0-9]+([-_]?\w+|))$', tmp):
            ticket = tmp

    # Get backup
    backup_source = select_backup(ticket)
    if backup_source is None:
        abort()

    # Determine restore method
    extract_item('wimlib', global_vars, silent=True)
    restore_source = None
    restore_options = []
    _file_based = False
    for item in os.scandir(backup_source.path):
        if item.is_dir():
            _file_based = True
            restore_options.append({'Name': 'File-Based:\t{source}'.format(source=item.name), 'Source': item})
            for _subitem in os.scandir(item.path):
                if is_valid_wim_image(_subitem):
                    restore_options.append({'Name': 'Image-Based: {dir}\\{source}'.format(dir=item.name, source=_subitem.name), 'Source': _subitem})
        elif is_valid_wim_image(item):
            restore_options.append({'Name': 'Image-Based:\t{source}'.format(source=item.name), 'Source': item})
    if _file_based:
        restore_options.append({'Name': 'File-Based:\t.', 'Source': backup_source})
    restore_options = sorted(restore_options, key=itemgetter('Name'))
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]
    if len(restore_options) > 0:
        selection = menu_select('Which backup are we using? (Path: {path})'.format(path=backup_source.path), restore_options, actions)
        if selection == 'Q':
            abort()
        else:
            restore_source = restore_options[int(selection)-1]['Source']
    else:
        print_error('ERROR: No restoration options detected.')
        abort()

    # Start transfer
    print_info('Using backup: {path}'.format(path=restore_source.path))
    if restore_source.is_dir():
        transfer_file_based(restore_source.path)
        # Check for Windows.old*
        for item in os.scandir(restore_source.path):
            if item.is_dir() and re.search(r'^Windows.old', item.name, re.IGNORECASE):
                transfer_file_based(item.path, subdir=item.name)
    if restore_source.is_file():
        transfer_image_based(restore_source.path)
    cleanup_transfer()

    # Done
    umount_backup_shares()
    print_success('Done.')
    run_kvrt()
    pause("Press Enter to exit...")
    exit_script(global_vars)
