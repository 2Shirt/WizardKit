# Wizard Kit PE: Functions - Data

import ctypes

from operator import itemgetter

from functions.common import *

# Classes
class LocalDisk():
    def __init__(self, disk):
        self.disk = disk
        self.name = disk.mountpoint.upper()
        self.path = self.name
    def is_dir(self):
        # Should always be true
        return True

# Regex
REGEX_EXCL_ITEMS = re.compile(
    r'^(\.(AppleDB|AppleDesktop|AppleDouble'
    r'|com\.apple\.timemachine\.supported|dbfseventsd'
    r'|DocumentRevisions-V100.*|DS_Store|fseventsd|PKInstallSandboxManager'
    r'|Spotlight.*|SymAV.*|symSchedScanLockxz|TemporaryItems|Trash.*'
    r'|vol|VolumeIcon\.icns)|desktop\.(ini|.*DB|.*DF)'
    r'|(hiberfil|pagefile)\.sys|lost\+found|Network\.*Trash\.*Folder'
    r'|Recycle[dr]|System\.*Volume\.*Information|Temporary\.*Items'
    r'|Thumbs\.db)$',
    re.IGNORECASE)
REGEX_EXCL_ROOT_ITEMS = re.compile(
    r'^\\?(boot(mgr|nxt)$|Config.msi'
    r'|(eula|globdata|install|vc_?red)'
    r'|.*.sys$|System Volume Information|RECYCLER?|\$Recycle\.bin'
    r'|\$?Win(dows(.old.*|\.~BT|)$|RE_)|\$GetCurrent|Windows10Upgrade'
    r'|PerfLogs|Program Files|SYSTEM.SAV'
    r'|.*\.(esd|swm|wim|dd|map|dmg|image)$)',
    re.IGNORECASE)
REGEX_INCL_ROOT_ITEMS = re.compile(
    r'^\\?(AdwCleaner|(My\s*|)(Doc(uments?( and Settings|)|s?)|Downloads'
    r'|Media|Music|Pic(ture|)s?|Vid(eo|)s?)'
    r'|{prefix}(-?Info|-?Transfer|)'
    r'|(ProgramData|Recovery|Temp.*|Users)$'
    r'|.*\.(log|txt|rtf|qb\w*|avi|m4a|m4v|mp4|mkv|jpg|png|tiff?)$)'
    r''.format(prefix=KIT_NAME_SHORT),
    re.IGNORECASE)
REGEX_WIM_FILE = re.compile(
    r'\.wim$',
    re.IGNORECASE)
REGEX_WINDOWS_OLD = re.compile(
    r'^\\Win(dows|)\.old',
    re.IGNORECASE)

# STATIC VARIABLES
FAST_COPY_EXCLUDES = [
    r'\*.esd',
    r'\*.swm',
    r'\*.wim',
    r'\*.dd',
    r'\*.dd.tgz',
    r'\*.dd.txz',
    r'\*.map',
    r'\*.dmg',
    r'\*.image',
    r'$RECYCLE.BIN',
    r'$Recycle.Bin',
    r'.AppleDB',
    r'.AppleDesktop',
    r'.AppleDouble',
    r'.com.apple.timemachine.supported',
    r'.dbfseventsd',
    r'.DocumentRevisions-V100*',
    r'.DS_Store',
    r'.fseventsd',
    r'.PKInstallSandboxManager',
    r'.Spotlight*',
    r'.SymAV*',
    r'.symSchedScanLockxz',
    r'.TemporaryItems',
    r'.Trash*',
    r'.vol',
    r'.VolumeIcon.icns',
    r'desktop.ini',
    r'Desktop?DB',
    r'Desktop?DF',
    r'hiberfil.sys',
    r'lost+found',
    r'Network?Trash?Folder',
    r'pagefile.sys',
    r'Recycled',
    r'RECYCLER',
    r'System?Volume?Information',
    r'Temporary?Items',
    r'Thumbs.db',
    ]
FAST_COPY_ARGS = [
    '/cmd=noexist_only',
    '/utf8',
    '/skip_empty_dir',
    '/linkdest',
    '/no_ui',
    '/auto_close',
    '/exclude={}'.format(';'.join(FAST_COPY_EXCLUDES)),
    ]
# Code borrowed from: https://stackoverflow.com/a/29075319
SEM_NORMAL = ctypes.c_uint()
SEM_FAILCRITICALERRORS = 1
SEM_NOOPENFILEERRORBOX = 0x8000
SEM_FAIL = SEM_NOOPENFILEERRORBOX | SEM_FAILCRITICALERRORS

def cleanup_transfer(dest_path):
    """Fix attributes and move extraneous items outside the Transfer folder."""
    try:
        # Remove dest_path if empty
        os.rmdir(dest_path)
    except OSError:
        pass
    if not os.path.exists(dest_path):
        # Bail if dest_path was empty and removed
        raise Exception
    
    # Fix attributes
    cmd = ['attrib', '-a', '-h', '-r', '-s', dest_path]
    run_program(cmd, check=False)
    
    for root, dirs, files in os.walk(dest_path, topdown=False):
        for name in dirs:
            # Remove empty directories and junction points
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass
        for name in files:
            # "Remove" files based on exclusion regex
            if REGEX_EXCL_ITEMS.search(name):
                # Make dest folder
                dest_name = root.replace(dest_path, dest_path+'.Removed')
                os.makedirs(dest_name, exist_ok=True)
                # Set dest filename
                dest_name = os.path.join(dest_name, name)
                dest_name = non_clobber_rename(dest_name)
                source_name = os.path.join(root, name)
                try:
                    shutil.move(source_name, dest_name)
                except Exception:
                    pass

def is_valid_wim_file(item):
    """Checks if the provided os.DirEntry is a valid WIM file, returns bool."""
    valid = bool(item.is_file() and REGEX_WIM_FILE.search(item.name))
    if valid:
        extract_item('wimlib', silent=True)
        cmd = [global_vars['Tools']['wimlib-imagex'], 'info', item.path]
        try:
            run_program(cmd)
        except subprocess.CalledProcessError:
            valid = False
            print_log('WARNING: Image "{}" damaged.'.format(item.name))
    return valid

def mount_backup_shares():
    """Mount the backup shares unless labeled as already mounted."""
    for server in BACKUP_SERVERS:
        # Blindly skip if we mounted earlier
        if server['Mounted']:
            continue
        
        mount_network_share(server)

def mount_network_share(server):
    """Mount a network share defined by server."""
    # Test connection
    try:
        ping(server['IP'])
    except subprocess.CalledProcessError:
        print_error(
            r'Failed to mount \\{Name}\{Share}, {IP} unreachable.'.format(
                **server))
        sleep(1)
        return False

    # Mount
    cmd = r'net use \\{IP}\{Share} /user:{User} {Pass}'.format(**server)
    cmd = cmd.split(' ')
    try:
        run_program(cmd)
    except Exception:
        print_warning(r'Failed to mount \\{Name}\{Share} ({IP})'.format(
            **server))
        sleep(1)
    else:
        print_info('Mounted {Name}'.format(**server))
        server['Mounted'] = True

def run_fast_copy(items, dest):
    """Copy items to dest using FastCopy."""
    if not items:
        raise Exception
    
    cmd = [global_vars['Tools']['FastCopy'], *FAST_COPY_ARGS]
    if 'LogFile' in global_vars:
        cmd.append('/logfile={LogFile}'.format(**global_vars))
    cmd.extend(items)
    cmd.append('/to={}\\'.format(dest))
    
    run_program(cmd)

def run_wimextract(source, items, dest):
    """Extract items from source WIM to dest folder."""
    if not items:
        raise Exception
    extract_item('wimlib', silent=True)

    # Write files.txt
    with open(r'{TmpDir}\wim_files.txt'.format(**global_vars), 'w') as f:
        # Defaults
        for item in items:
            f.write('{item}\n'.format(item=item))
    sleep(1) # For safety?

    # Extract files
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'extract',
        source, '1',
        r'@{TmpDir}\wim_files.txt'.format(**global_vars),
        '--dest-dir={}\\'.format(dest),
        '--no-acls',
        '--nullglob']
    run_program(cmd)

def scan_source(source_obj, dest_path):
    """Scan source for files/folders to transfer."""
    selected_items = []
    
    if source_obj.is_dir():
        # File-Based
        print_standard('Scanning source (folder): {}'.format(source_obj.path))
        selected_items = scan_source_path(source_obj.path, dest_path)
    else:
        # Image-Based
        if REGEX_WIM_FILE.search(source_obj.name):
            print_standard('Scanning source (image): {}'.format(
                source_obj.path))
            selected_items = scan_source_wim(source_obj.path, dest_path)
        else:
            print_error('ERROR: Unsupported image: {}'.format(
                source_obj.path))
            raise GenericError
    
    return selected_items

def scan_source_path(source_path, dest_path, rel_path=None, interactive=True):
    """Scan source folder for files/folders to transfer, returns list.
    
    This will scan the root and (recursively) any Windows.old folders."""
    rel_path = '\\' + rel_path if rel_path else ''
    if rel_path:
        dest_path = dest_path + rel_path
    selected_items = []
    win_olds = []

    # Root items
    root_items = []
    for item in os.scandir(source_path):
        if REGEX_INCL_ROOT_ITEMS.search(item.name):
            root_items.append(item.path)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item.name):
            if (not interactive
                or ask('Copy: "{}{}" ?'.format(rel_path, item.name))):
                root_items.append(item.path)
        if REGEX_WINDOWS_OLD.search(item.name):
            win_olds.append(item)
    if root_items:
        selected_items.append({
            'Message':      '{}Root Items...'.format(rel_path),
            'Items':        root_items.copy(),
            'Destination':  dest_path})

    # Fonts
    if os.path.exists(r'{}\Windows\Fonts'.format(source_path)):
        selected_items.append({
            'Message':      '{}Fonts...'.format(rel_path),
            'Items':        [r'{}\Windows\Fonts'.format(rel_path)],
            'Destination':  r'{}\Windows'.format(dest_path)})

    # Registry
    registry_items = []
    for folder in ['config', 'OEM']:
        folder = r'Windows\System32\{}'.format(folder)
        folder = os.path.join(source_path, folder)
        if os.path.exists(folder):
            registry_items.append(folder)
    if registry_items:
        selected_items.append({
            'Message': '{}Registry...'.format(rel_path),
            'Items':        registry_items.copy(),
            'Destination':  r'{}\Windows\System32'.format(dest_path)})

    # Windows.old(s)
    for old in win_olds:
        selected_items.append(
            scan_source_path(
                old.path, dest_path, rel_path=old.name, interactive=False))
    
    # Done
    return selected_items

def scan_source_wim(source_wim, dest_path, rel_path=None, interactive=True):
    """Scan source WIM file for files/folders to transfer, returns list.
    
    This will scan the root and (recursively) any Windows.old folders."""
    rel_path = '\\' + rel_path if rel_path else ''
    selected_items = []
    win_olds = []

    # Scan source
    extract_item('wimlib', silent=True)
    cmd = [
        global_vars['Tools']['wimlib-imagex'], 'dir',
        source_wim, '1']
    try:
        file_list = run_program(cmd)
    except subprocess.CalledProcessError:
        print_error('ERROR: Failed to get file list.')
        raise

    # Root Items
    file_list = [i.strip()
        for i in file_list.stdout.decode('utf-8', 'ignore').splitlines()
        if i.count('\\') == 1 and i.strip() != '\\']
    root_items = []
    if rel_path:
        file_list = [i.replace(rel_path, '') for i in file_list]
    for item in file_list:
        if REGEX_INCL_ROOT_ITEMS.search(item):
            root_items.append(item)
        elif not REGEX_EXCL_ROOT_ITEMS.search(item):
            if (not interactive
                or ask('Extract: "{}{}" ?'.format(rel_path, item))):
                root_items.append('{}{}'.format(rel_path, item))
        if REGEX_WINDOWS_OLD.search(item):
            win_olds.append(item)
    if root_items:
        selected_items.append({
            'Message':      '{}Root Items...'.format(rel_path),
            'Items':        root_items.copy(),
            'Destination':  dest_path})

    # Fonts
    if wim_contains(source_wim, r'{}Windows\Fonts'.format(rel_path)):
        selected_items.append({
            'Message':      '{}Fonts...'.format(rel_path),
            'Items':        [r'{}\Windows\Fonts'.format(rel_path)],
            'Destination':  dest_path})

    # Registry
    registry_items = []
    for folder in ['config', 'OEM']:
        folder = r'{}Windows\System32\{}'.format(rel_path, folder)
        if wim_contains(source_wim, folder):
            registry_items.append(folder)
    if registry_items:
        selected_items.append({
            'Message':      '{}Registry...'.format(rel_path),
            'Items':        registry_items.copy(),
            'Destination':  dest_path})

    # Windows.old(s)
    for old in win_olds:
        scan_source_wim(source_wim, dest_path, rel_path=old, interactive=False)
    
    # Done
    return selected_items

def select_destination(folder_path, prompt='Select destination'):
    """Select destination drive, returns path as string."""
    disk = select_volume(prompt)
    if 'fixed' not in disk['Disk'].opts:
        folder_path = folder_path.replace('\\', '-')
    path = '{disk}{folder_path}_{Date}'.format(
        disk = disk['Disk'].mountpoint,
        folder_path = folder_path,
        **global_vars)

    # Avoid merging with existing folder
    path = non_clobber_rename(path)
    os.makedirs(path, exist_ok=True)

    return path

def select_source(ticket_number):
    """Select backup from those found on the BACKUP_SERVERS for the ticket."""
    selected_source = None
    sources = []
    mount_backup_shares()

    # Check for ticket folders on servers
    for server in BACKUP_SERVERS:
        if server['Mounted']:
            print_standard('Scanning {}...'.format(server['Name']))
            for d in os.scandir(r'\\{IP}\{Share}'.format(**server)):
                if (d.is_dir()
                    and d.name.lower().startswith(ticket_number.lower())):
                    # Add folder to sources
                    sources.append({
                        'Name': '{:9}| File-Based:     [DIR]  {}'.format(
                            server['Name'], d.name),
                        'Server': server,
                        'Source': d})

    # Check for images and subfolders
    for ticket_path in sources.copy():
        for item in os.scandir(ticket_path['Source'].path):
            if item.is_dir():
                # Add folder to sources
                sources.append({
                    'Name': r'{:9}| File-Based:     [DIR]  {}\{}'.format(
                        ticket_path['Server']['Name'],  # Server
                        ticket_path['Source'].name,     # Ticket folder
                        item.name,                      # Sub-folder
                        ),
                    'Server': ticket_path['Server'],
                    'Source': item})

                # Check for images in folder
                for subitem in os.scandir(item.path):
                    if REGEX_WIM_FILE.search(item.name):
                        # Add image to sources
                        try:
                            size = human_readable_size(item.stat().st_size)
                        except Exception:
                            size = '  ?  ?' # unknown
                        sources.append({
                            'Disabled': bool(not is_valid_wim_file(subitem)),
                            'Name': r'{:9}| Image-Based:  {:>7}  {}\{}\{}'.format(
                                ticket_path['Server']['Name'],  # Server
                                size,                           # Size (duh)
                                ticket_path['Source'].name,     # Ticket folder
                                item.name,                      # Sub-folder
                                subitem.name,                   # Image file
                                ),
                            'Server': ticket_path['Server'],
                            'Source': subitem})
            elif REGEX_WIM_FILE.search(item.name):
                # Add image to sources
                try:
                    size = human_readable_size(item.stat().st_size)
                except Exception:
                    size = '  ?  ?' # unknown
                sources.append({
                    'Disabled': bool(not is_valid_wim_file(item)),
                    'Name': r'{:9}| Image-Based:  {:>7}  {}\{}'.format(
                        ticket_path['Server']['Name'],  # Server
                        size,                           # Size (duh)
                        ticket_path['Source'].name,     # Ticket folder
                        item.name,                      # Image file
                        ),
                    'Server': ticket_path['Server'],
                    'Source': item})
    # Check for local sources
    print_standard('Scanning for local sources...')
    set_thread_error_mode(silent=True) # Prevents "No disk" popups
    sys_drive = global_vars['Env']['SYSTEMDRIVE']
    for d in psutil.disk_partitions():
        if re.search(r'^{}'.format(sys_drive), d.mountpoint, re.IGNORECASE):
            # Skip current OS drive
            continue
        if 'fixed' in d.opts:
            # Skip DVD, etc
            sources.append({
                'Name': '{:9}| File-Based:     [DISK] {}'.format(
                    '  Local', d.mountpoint),
                'Source': LocalDisk(d)})
    set_thread_error_mode(silent=False) # Return to normal

    # Build Menu
    sources.sort(key=itemgetter('Name'))
    actions = [{'Name': 'Quit', 'Letter': 'Q'}]

    # Select backup from sources
    if len(sources) > 0:
        selection = menu_select(
            'Which backup are we using?',
            main_entries=sources,
            action_entries=actions,
            disabled_label='DAMAGED')
        if selection == 'Q':
            umount_backup_shares()
            exit_script()
        else:
            selected_source = sources[int(selection)-1]['Source']
    else:
        print_error('ERROR: No backups found for ticket: {}.'.format(
            ticket_number))
        umount_backup_shares()
        pause("Press Enter to exit...")
        exit_script()
    
    # Done
    return selected_source

def select_volume(title='Select disk', auto_select=True):
    """Select disk from attached disks. returns dict."""
    actions =   [{'Name': 'Quit', 'Letter': 'Q'}]
    disks =     []
    
    # Build list of disks
    set_thread_error_mode(silent=True) # Prevents "No disk" popups
    for d in psutil.disk_partitions():
        info = {
            'Disk': d,
            'Name': d.mountpoint}
        try:
            usage = psutil.disk_usage(d.device)
            free = '{free} / {total} available'.format(
                free = human_readable_size(usage.free, 2),
                total = human_readable_size(usage.total, 2))
        except Exception:
            # Meh, leaving unsupported destinations out
            pass
            # free = 'Unknown'
            # info['Disabled'] = True
        else:
            info['Display Name'] = '{}  ({})'.format(info['Name'], free)
            disks.append(info)
    set_thread_error_mode(silent=False) # Return to normal
    
    # Skip menu?
    if len(disks) == 1 and auto_select:
        return disks[0]
    
    # Show menu
    selection = menu_select(title, main_entries=disks, action_entries=actions)
    if selection == 'Q':
        exit_script()
    else:
        return disks[int(selection)-1]

def set_thread_error_mode(silent=True):
    """Disable or Enable Windows error message dialogs.
    
    Disable when scanning for disks to avoid popups for empty cardreaders, etc
    """
    # Code borrowed from: https://stackoverflow.com/a/29075319
    kernel32 = ctypes.WinDLL('kernel32')
    
    if silent:
        kernel32.SetThreadErrorMode(SEM_FAIL, ctypes.byref(SEM_NORMAL))
    else:
        kernel32.SetThreadErrorMode(SEM_NORMAL, ctypes.byref(SEM_NORMAL))

def transfer_source(source_obj, dest_path, selected_items):
    """Transfer, or extract, files/folders from source to destination."""
    if source_obj.is_dir():
        # Run FastCopy for each selection "group"
        for group in selected_items:
            try_and_print(message=group['Message'],
                function=run_fast_copy, cs='Done',
                items=group['Items'],
                dest=group['Destination'])
    else:
        if REGEX_WIM_FILE.search(source_obj.name):
            # Extract files from WIM
            for group in selected_items:
                try_and_print(message=group['Message'],
                    function=run_wimextract, cs='Done',
                    source=source_obj.path,
                    items=group['Items'],
                    dest=group['Destination'])
        else:
            print_error('ERROR: Unsupported image: {}'.format(source_obj.path))
            raise GenericError

def umount_backup_shares():
    """Unnount the backup shares regardless of current status."""
    for server in BACKUP_SERVERS:
        umount_network_share(server)

def umount_network_share(server):
    """Unnount a network share defined by server."""
    cmd = r'net use \\{IP}\{Share} /delete'.format(**server)
    cmd = cmd.split(' ')
    try:
        run_program(cmd)
    except Exception:
        print_error(r'Failed to umount \\{Name}\{Share}.'.format(**server))
        sleep(1)
    else:
        print_info('Umounted {Name}'.format(**server))
        server['Mounted'] = False

def wim_contains(source_path, file_path):
    """Check if the WIM contains a file or folder."""
    _cmd = [
        global_vars['Tools']['wimlib-imagex'], 'dir',
        source_path, '1',
        '--path={}'.format(file_path),
        '--one-file-only']
    try:
        run_program(_cmd)
    except subprocess.CalledProcessError:
        return False
    else:
        return True

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
