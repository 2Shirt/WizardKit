# Wizard Kit: Copy user data to the system over the network

import os
import re
from operator import itemgetter

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Data 1')
from functions import *
vars_wk = init_vars_wk()
vars_wk.update(init_vars_os())
vars_wk['LogFile'] = '{LogDir}\\Data 1.log'.format(**vars_wk)
os.makedirs('{LogDir}'.format(**vars_wk), exist_ok=True)
vars_wk['TransferDir'] = '{ClientDir}\\Transfer'.format(**vars_wk)
vars_wk['FastCopy'] = '{BinDir}\\FastCopy\\FastCopy.exe'.format(**vars_wk)
vars_wk['FastCopyArgs'] = [
    '/cmd=noexist_only',
    '/logfile={LogFile}'.format(**vars_wk),
    '/utf8',
    '/skip_empty_dir',
    '/linkdest',
    '/no_ui',
    '/auto_close',
    '/exclude=\\*.esd;\\*.swm;\\*.wim;\\*.dd;\\*.dd.tgz;\\*.dd.txz;\\*.map;\\*.dmg;\\*.image;$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']
vars_wk['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars_wk)
vars_wk['wimlib-imagex'] = '{BinDir}\\wimlib\\x32\\wimlib-imagex.exe'.format(**vars_wk)
if vars_wk['Arch'] == 64:
    vars_wk['FastCopy'] = vars_wk['FastCopy'].replace('FastCopy.exe', 'FastCopy64.exe')
    vars_wk['Notepad2'] = vars_wk['Notepad2'].replace('Notepad2-Mod.exe', 'Notepad2-Mod64.exe')
    vars_wk['wimlib-imagex'] = vars_wk['wimlib-imagex'].replace('x32', 'x64')
re_included_root_items = re.compile(r'^\\(AdwCleaner|(My\s*|)(Doc(uments?( and Settings|)|s?)|Downloads|WK(-?Info|-?Transfer|)|Media|Music|Pic(ture|)s?|Vid(eo|)s?)|(ProgramData|Recovery|Temp.*|Users)$|.*\.(log|txt|rtf|qb\w*|avi|m4a|m4v|mp4|mkv|jpg|png|tiff?)$)', flags=re.IGNORECASE)
re_excluded_root_items = re.compile(r'^\\(boot(mgr|nxt)$|(eula|globdata|install|vc_?red)|.*.sys$|System Volume Information|RECYCLER|\$Recycle\.bin|\$?Win(dows(.old|\.~BT|)$|RE_)|\$GetCurrent|PerfLogs|Program Files|.*\.(esd|swm|wim|dd|map|dmg|image)$|SYSTEM.SAV|Windows10Upgrade)', flags=re.IGNORECASE)
re_excluded_items = re.compile(r'^(\.(AppleDB|AppleDesktop|AppleDouble|com\.apple\.timemachine\.supported|dbfseventsd|DocumentRevisions-V100.*|DS_Store|fseventsd|PKInstallSandboxManager|Spotlight.*|SymAV.*|symSchedScanLockxz|TemporaryItems|Trash.*|vol|VolumeIcon\.icns)|desktop\.(ini|.*DB|.*DF)|(hiberfil|pagefile)\.sys|lost\+found|Network\.*Trash\.*Folder|Recycle[dr]|System\.*Volume\.*Information|Temporary\.*Items|Thumbs\.db)$', flags=re.IGNORECASE)
wim_included_extra_items = [
    'AdwCleaner\\*log',
    'AdwCleaner\\*txt',
    '\\Windows.old*\\Doc*',
    '\\Windows.old*\\Download*',
    '\\Windows.old*\\WK*',
    '\\Windows.old*\\Media*',
    '\\Windows.old*\\Music*',
    '\\Windows.old*\\Pic*',
    '\\Windows.old*\\ProgramData',
    '\\Windows.old*\\Recovery',
    '\\Windows.old*\\Temp*',
    '\\Windows.old*\\Users',
    '\\Windows.old*\\Vid*',
    '\\Windows.old*\\Windows\\System32\\OEM',
    '\\Windows.old*\\Windows\\System32\\config',
    '\\Windows\\System32\\OEM',
    '\\Windows\\System32\\config']

def abort():
    print_warning('Aborted.', vars_wk['LogFile'])
    exit_script()

def cleanup_transfer():
    """Fix permissions and walk through transfer folder (from the bottom) and remove extraneous items."""
    run_program('attrib -a -h -r -s "{TransferDir}"'.format(**vars_wk), check=False)
    if os.path.exists(vars_wk['TransferDir']):
        for root, dirs, files in os.walk(vars_wk['TransferDir'], topdown=False):
            for name in dirs:
                # Remove empty directories and junction points
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
            for name in files:
                # Remove files based on exclusion regex
                if re_excluded_items.search(name):
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass

def exit_script():
    umount_backup_shares()
    pause("Press Enter to exit...")
    extract_item('Notepad2', vars_wk, silent=True)
    subprocess.Popen('"{Notepad2}" "{LogFile}"'.format(**vars_wk))
    quit()

def is_valid_image(item):
    _valid = item.is_file() and re.search(r'\.wim$', item.name, flags=re.IGNORECASE)
    if _valid:
        try:
            _cmd = [vars_wk['wimlib-imagex'], 'info', '{image}'.format(image=item.path)]
            run_program(_cmd)
        except subprocess.CalledProcessError:
            _valid = False
            print_warning('WARNING: Image damaged.', vars_wk['LogFile'])
            time.sleep(2)
    return _valid

def transfer_file_based(source_path, subdir=None):
    # Set Destination
    if subdir is None:
        dest_path = vars_wk['TransferDir']
    else:
        dest_path = '{TransferDir}\\{subdir}'.format(subdir=subdir, **vars_wk)
    os.makedirs(dest_path, exist_ok=True)
    
    # Main copy
    selected_items = []
    for item in os.scandir(source_path):
        if re_included_root_items.search(item.name):
            selected_items.append(item.path)
        elif not re_excluded_root_items.search(item.name):
            if ask('Copy: "{name}" item?'.format(name=item.name)):
                selected_items.append(item.path)
    if len(selected_items) > 0:
        _args = vars_wk['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying main user data...', vars_wk['LogFile'])
            run_program(vars_wk['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying main user data', vars_wk['LogFile'])
    else:
        print_error('ERROR: No files selected for transfer?', vars_wk['LogFile'])
        abort()

    # Fonts
    selected_items = []
    if os.path.exists('{source}\\Windows\\Fonts'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\Fonts'.format(source=source_path))
    if len(selected_items) > 0:
        _args = vars_wk['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\Windows\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying Fonts...', vars_wk['LogFile'])
            run_program(vars_wk['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying Fonts', vars_wk['LogFile'])

    # Registry
    selected_items = []
    if os.path.exists('{source}\\Windows\\System32\\config'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\System32\\config'.format(source=source_path))
    if os.path.exists('{source}\\Windows\\System32\\OEM'.format(source=source_path)):
        selected_items.append('{source}\\Windows\\System32\\OEM'.format(source=source_path))
    if len(selected_items) > 0:
        _args = vars_wk['FastCopyArgs'].copy() + selected_items
        _args.append('/to={dest_path}\\Windows\\System32\\'.format(dest_path=dest_path))
        try:
            print_standard('Copying Registry...', vars_wk['LogFile'])
            run_program(vars_wk['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying registry', vars_wk['LogFile'])

def transfer_image_based(source_path):
    print_standard('Assessing image...', vars_wk['LogFile'])
    os.makedirs(vars_wk['TransferDir'], exist_ok=True)

    # Scan source
    _args = [
        'dir',
        '{source}'.format(source=source_path), '1']
    try:
        _list = run_program(vars_wk['wimlib-imagex'], _args, check=True)
    except subprocess.CalledProcessError as err:
        print_error('ERROR: Failed to get file list.', vars_wk['LogFile'])
        print(err)
        abort()

    # Add items to list
    selected_items = []
    root_items = [i.strip() for i in _list.stdout.decode('utf-8', 'ignore').splitlines() if i.count('\\') == 1 and i.strip() != '\\']
    for item in root_items:
        if re_included_root_items.search(item):
            selected_items.append(item)
        elif not re_excluded_root_items.search(item):
            if ask('Extract: "{name}" item?'.format(name=item)):
                selected_items.append(item)

    # Extract files
    if len(selected_items) > 0:
        # Write files.txt
        with open('{TmpDir}\\wim_files.txt'.format(**vars_wk), 'w') as f:
            # Defaults
            for item in wim_included_extra_items:
                f.write('{item}\n'.format(item=item))
            for item in selected_items:
                f.write('{item}\n'.format(item=item))
        try:
            print_standard('Extracting user data...', vars_wk['LogFile'])
            _args = [
                'extract',
                '{source}'.format(source=source_path), '1',
                '@{TmpDir}\\wim_files.txt'.format(**vars_wk),
                '--dest-dir={TransferDir}\\'.format(**vars_wk),
                '--no-acls',
                '--nullglob']
            run_program(vars_wk['wimlib-imagex'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while extracting user data', vars_wk['LogFile'])
    else:
        print_error('ERROR: No files selected for extraction?', vars_wk['LogFile'])
        abort()

if __name__ == '__main__':
    stay_awake(vars_wk)
    # Check for existing TransferDir
    if os.path.exists(vars_wk['TransferDir']):
        print_warning('Folder "{TransferDir}" exists. This script will rename the existing folder in order to avoid overwriting data.'.format(**vars_wk), vars_wk['LogFile'])
        if (ask('Rename existing folder and proceed?', vars_wk['LogFile'])):
            _old_transfer = '{TransferDir}.old'.format(**vars_wk)
            _i = 1;
            while os.path.exists(_old_transfer):
                _old_transfer = '{TransferDir}.old{i}'.format(i=_i, **vars_wk)
                _i += 1
            print_info('Renaming "{TransferDir}" to "{old_transfer}"'.format(old_transfer=_old_transfer, **vars_wk), vars_wk['LogFile'])
            os.rename(vars_wk['TransferDir'], _old_transfer)
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
    extract_item('wimlib', vars_wk, silent=True)
    restore_source = None
    restore_options = []
    _file_based = False
    for item in os.scandir(backup_source.path):
        if item.is_dir():
            _file_based = True
            restore_options.append({'Name': 'File-Based:\t{source}'.format(source=item.name), 'Source': item})
            for _subitem in os.scandir(item.path):
                if is_valid_image(_subitem):
                    restore_options.append({'Name': 'Image-Based: {dir}\\{source}'.format(dir=item.name, source=_subitem.name), 'Source': _subitem})
        elif is_valid_image(item):
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
        print_error('ERROR: No restoration options detected.', vars_wk['LogFile'])
        abort()

    # Start transfer
    print_info('Using backup: {path}'.format(path=restore_source.path), vars_wk['LogFile'])
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
    print_success('Done.', vars_wk['LogFile'])
    kill_process('caffeine.exe')
    exit_script()
