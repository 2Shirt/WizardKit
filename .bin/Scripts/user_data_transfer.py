# Wizard Kit: Copy user data to the system over the network

import os
import re
from operator import itemgetter

# Init
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.system('title Wizard Kit: Data 1')
from functions import *
vars = init_vars()
vars_os = init_vars_os()
vars['LogFile'] = '{LogDir}\\Data 1.log'.format(**vars)
os.makedirs('{LogDir}'.format(**vars), exist_ok=True)
vars['TransferDir'] = '{ClientDir}\\Transfer\\'.format(**vars)
os.makedirs('{TransferDir}'.format(**vars), exist_ok=True)
vars['FastCopy'] = '{BinDir}\\FastCopy\\FastCopy.exe'.format(**vars)
vars['FastCopyArgs'] = [
    '/cmd=noexist_only',
    '/logfile={LogFile}'.format(**vars),
    '/utf8',
    '/skip_empty_dir',
    '/linkdest',
    '/no_ui',
    '/auto_close',
    '/exclude=\\*.esd;\\*.swm;\\*.wim;\\*.dd;\\*.dd.tgz;\\*.dd.txz;\\*.map;\\*.dmg;\\*.image;$RECYCLE.BIN;$Recycle.Bin;.AppleDB;.AppleDesktop;.AppleDouble;.com.apple.timemachine.supported;.dbfseventsd;.DocumentRevisions-V100*;.DS_Store;.fseventsd;.PKInstallSandboxManager;.Spotlight*;.SymAV*;.symSchedScanLockxz;.TemporaryItems;.Trash*;.vol;.VolumeIcon.icns;desktop.ini;Desktop?DB;Desktop?DF;hiberfil.sys;lost+found;Network?Trash?Folder;pagefile.sys;Recycled;RECYCLER;System?Volume?Information;Temporary?Items;Thumbs.db']
vars['Notepad2'] = '{BinDir}\\Notepad2\\Notepad2-Mod.exe'.format(**vars)
vars['wimlib-imagex'] = '{BinDir}\\wimlib\\x32\\wimlib-imagex.exe'.format(**vars)
if vars_os['Arch'] == 64:
    vars['FastCopy'] = vars['FastCopy'].replace('FastCopy.exe', 'FastCopy64.exe')
    vars['Notepad2'] = vars['Notepad2'].replace('Notepad2-Mod.exe', 'Notepad2-Mod64.exe')
    vars['wimlib-imagex'] = vars['wimlib-imagex'].replace('x32', 'x64')
re_included_root_items = re.compile(r'(^\\((My\s*)|Downloads|Doc(uments?|s?)|WK(-Info|-Transfer|)|Media|Music|Pictures?|Videos?)$|^\\(ProgramData|Recovery|Temp.*|Users)$|(log|txt|rtf|qb\w*|avi|m4a|m4v|mp4|mkv|jpg|png|tiff?)$)', flags=re.IGNORECASE)
re_excluded_root_items = re.compile(r'(^\\boot(mgr|nxt)$|^\\(eula|globdata|install|vc_?red)|.*.sys$|^\\System Volume Information|RECYCLER|\$Recycle\.bin|^\\\$?Win(dows(.old|\.~BT|)$|RE_)|^\\PerfLogs|^\\Program Files|\.(esd|swm|wim|dd|map|dmg|image)$)', flags=re.IGNORECASE)
re_excluded_items = re.compile(r'^(\.(AppleDB|AppleDesktop|AppleDouble|com\.apple\.timemachine\.supported|dbfseventsd|DocumentRevisions-V100.*|DS_Store|fseventsd|PKInstallSandboxManager|Spotlight.*|SymAV.*|symSchedScanLockxz|TemporaryItems|Trash.*|vol|VolumeIcon\.icns)|desktop\.(ini|.*DB|.*DF)|(hiberfil|pagefile)\.sys|lost\+found|Network\.*Trash\.*Folder|Recycle[dr]|System\.*Volume\.*Information|Temporary\.*Items|Thumbs\.db)$', flags=re.IGNORECASE)

def abort():
    print_warning('Aborted.', log_file=vars['LogFile'])
    exit_script()

def cleanup_transfer():
    """Walk through transfer folder (from the bottom) and remove extraneous items."""
    if os.path.exists(vars['TransferDir']):
        for root, dirs, files in os.walk(vars['TransferDir'], topdown=False):
            for name in dirs:
                try:
                    # Removes empty directories and junction points
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
            for name in files:
                if re_excluded_items.search(name):
                    try:
                        # Removes files based on exclusion regex
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass

def exit_script():
    umount_backup_shares()
    pause("Press Enter to exit...")
    subprocess.Popen('"{Notepad2}" "{LogFile}"'.format(**vars))
    quit()

def is_valid_image(item):
    _valid = item.is_file() and re.search(r'\.wim$', item.name, flags=re.IGNORECASE)
    if _valid:
        try:
            _cmd = [vars['wimlib-imagex'], 'info', '{image}'.format(image=item.path)]
            run_program(_cmd)
        except subprocess.CalledProcessError:
            _valid = False
            print_warning('WARNING: Image damaged.', log_file=vars['LogFile'])
            time.sleep(2)
    return _valid

def transfer_file_based(restore_source):
    # Registry
    _args = vars['FastCopyArgs'].copy()
    if os.path.exists('{source}\\Windows\\System32\\config'.format(source=restore_source.path)):
        _args.append('{source}\\Windows\\System32\\config'.format(source=restore_source.path))
    if os.path.exists('{source}\\Windows\\System32\\OEM'.format(source=restore_source.path)):
        _args.append('{source}\\Windows\\System32\\OEM'.format(source=restore_source.path))
    _args.append('/to={TransferDir}\\Windows\\System32\\'.format(**vars))
    try:
        print_standard('Copying Windows Registry...', log_file=vars['LogFile'])
        run_program(vars['FastCopy'], _args, check=True)
    except subprocess.CalledProcessError:
        print_warning('WARNING: Errors encountered while copying registry', log_file=vars['LogFile'])
    
    # Registry (Windows.old)
    _args = vars['FastCopyArgs'].copy()
    if os.path.exists('{source}\\Windows.old\\Windows\\System32\\config'.format(source=restore_source.path)):
        _args.append('{source}\\Windows.old\\Windows\\System32\\config'.format(source=restore_source.path))
    if os.path.exists('{source}\\Windows.old\\Windows\\System32\\OEM'.format(source=restore_source.path)):
        _args.append('{source}\\Windows.old\\Windows\\System32\\OEM'.format(source=restore_source.path))
    _args.append('/to={TransferDir}\\Windows.old\\Windows\\System32\\'.format(**vars))
    try:
        print_standard('Copying Windows Registry...', log_file=vars['LogFile'])
        run_program(vars['FastCopy'], _args, check=True)
    except subprocess.CalledProcessError:
        print_warning('WARNING: Errors encountered while copying registry', log_file=vars['LogFile'])
    
    # Main copy
    selected_items = []
    for item in os.scandir(restore_source.path):
        if re_included_root_items.search(item.name):
            selected_items.append(item.path)
        elif not re_excluded_root_items.search(item.name):
            if ask('Copy: "{name}" item?'.format(name=item.name)):
                selected_items.append(item.path)
    if len(selected_items) > 0:
        _args = vars['FastCopyArgs'].copy()
        _args += selected_items
        _args.append('/to={TransferDir}\\'.format(**vars))
        try:
            print_standard('Copying main user data...', log_file=vars['LogFile'])
            run_program(vars['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying main user data', log_file=vars['LogFile'])
    else:
        print_error('ERROR: No files selected for transfer?', log_file=vars['LogFile'])
        abort()
    
    # Windows.old
    selected_items = []
    for item in ['Users', 'ProgramData']:
        item = '{source}\\Windows.old\\{item}'.format(source=restore_source.path, item=item)
        if os.path.exists(item):
            selected_items.append(item)
    if len(selected_items) > 0:
        _args = vars['FastCopyArgs'].copy()
        _args += selected_items
        _args.append('/to={TransferDir}\\Windows.old\\'.format(**vars))
        try:
            print_standard('Copying user data (Windows.old)...', log_file=vars['LogFile'])
            run_program(vars['FastCopy'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while copying data from Windows.old', log_file=vars['LogFile'])

def transfer_image_based(restore_source):
    print_standard('Assessing image...', log_file=vars['LogFile'])
    
    # Scan source
    _args = [
        'dir',
        '{source}'.format(source=restore_source.path), '1']
    try:
        _list = run_program(vars['wimlib-imagex'], _args, check=True)
    except subprocess.CalledProcessError as err:
        print_error('ERROR: Failed to get file list.')
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
        with open('{TmpDir}\\wim_files.txt'.format(**vars), 'w') as f:
            # Defaults
            f.write('\\Windows.old\\WK*\n')
            f.write('\\Windows.old\\ProgramData\n')
            f.write('\\Windows.old\\Temp\n')
            f.write('\\Windows.old\\Users\n')
            f.write('\\Windows.old\\Windows\\System32\\config\n')
            f.write('\\Windows.old\\Windows\\System32\\OEM\n')
            f.write('\\Windows\\System32\\config\n')
            f.write('\\Windows\\System32\\OEM\n')
            f.write('AdwCleaner\\*log\n')
            f.write('AdwCleaner\\*txt\n')
            for item in selected_items:
                f.write('{item}\n'.format(item=item))
        try:
            print_standard('Extracting user data...', log_file=vars['LogFile'])
            _args = [
                'extract',
                '{source}'.format(source=restore_source.path), '1',
                '@{TmpDir}\\wim_files.txt'.format(**vars),
                '--dest-dir={TransferDir}\\'.format(**vars),
                '--no-acls',
                '--nullglob']
            run_program(vars['wimlib-imagex'], _args, check=True)
        except subprocess.CalledProcessError:
            print_warning('WARNING: Errors encountered while extracting user data', log_file=vars['LogFile'])
    else:
        print_error('ERROR: No files selected for extraction?', log_file=vars['LogFile'])
        abort()

if __name__ == '__main__':
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
        print_error('ERROR: No restoration options detected.', log_file=vars['LogFile'])
        abort()
    
    # Start transfer
    print_info('Using backup: {path}'.format(path=restore_source.path), log_file=vars['LogFile'])
    if restore_source.is_dir():
        transfer_file_based(restore_source)
    if restore_source.is_file():
        transfer_image_based(restore_source)
    cleanup_transfer()
    
    # Done
    print_success('Done.', log_file=vars['LogFile'])
    exit_script()