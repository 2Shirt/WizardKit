# Wizard Kit PE: Functions - Windows Setup

from functions.data import *

# STATIC VARIABLES
DISKPART_SCRIPT = r'{}\diskpart.script'.format(global_vars['Env']['TMP'])
WINDOWS_VERSIONS = [
    {'Name': 'Windows 7 Home Basic',
        'Image File': 'Win7',
        'Image Name': 'Windows 7 HOMEBASIC'},
    {'Name': 'Windows 7 Home Premium',
        'Image File': 'Win7',
        'Image Name': 'Windows 7 HOMEPREMIUM'},
    {'Name': 'Windows 7 Professional', 
        'Image File': 'Win7', 
        'Image Name': 'Windows 7 PROFESSIONAL'},
    {'Name': 'Windows 7 Ultimate', 
        'Image File': 'Win7', 
        'Image Name': 'Windows 7 ULTIMATE'},
    
    {'Name': 'Windows 8.1', 
        'Image File': 'Win8', 
        'Image Name': 'Windows 8.1',
        'CRLF': True},
    {'Name': 'Windows 8.1 Pro', 
        'Image File': 'Win8', 
        'Image Name': 'Windows 8.1 Pro'},
    
    {'Name': 'Windows 10 Home', 
        'Image File': 'Win10', 
        'Image Name': 'Windows 10 Home',
        'CRLF': True},
    {'Name': 'Windows 10 Pro', 
        'Image File': 'Win10', 
        'Image Name': 'Windows 10 Pro'},
    ]

def find_windows_image(windows_version):
    """Search for a Windows source image file, returns dict.

    Searches on local disks and then the WINDOWS_SERVER share."""
    image = {}
    imagefile = windows_version['Image File']
    imagename = windows_version['Image Name']

    # Search local source
    for d in psutil.disk_partitions():
        for ext in ['esd', 'wim', 'swm']:
            path = '{}images\{}.{}'.format(d.mountpoint, imagefile, ext)
            if os.path.isfile(path) and wim_contains_image(path, imagename):
                image['Path'] = path
                image['Source'] = letter
                if ext == 'swm':
                    image['Glob'] = '--ref="{}*.swm"'.format(image['Path'][:-4])
                break

    # Check for network source
    if not image:
        mount_windows_share()
        if not WINDOWS_SERVER['Mounted']:
            return None
        for ext in ['esd', 'wim', 'swm']:
            path = r'\\{}\{}\images\{}.ext'.format(
                WINDOWS_SERVER['IP'], WINDOWS_SERVER['Share'], imagefile, ext)
            if os.path.isfile(path) and wim_contains_image(path, imagename):
                image['Path'] = path
                image['Source'] = None
                if ext == 'swm':
                    image['Glob'] = '--ref="{}*.swm"'.format(image['Path'][:-4])
                break
    
    # Display image to be used (if any) and return
    if image:
        print_info('Using image: {}'.format(image['Path']))
        return image
    else:
        print_error('Failed to find Windows source image for {}'.format(
            windows_version['Name']))
        raise GeneralAbort

def format_disk(disk, use_gpt):
    """Format disk for use as a Windows OS disk."""
    if use_gpt:
        format_gpt(disk)
    else:
        format_mbr(disk)

def format_gpt(disk):
    """Format disk for use as a Windows OS disk using the GPT layout."""
    with open(DISKPART_SCRIPT, 'w') as script:
        # Partition table
        script.write('select disk {}\n'.format(disk['Number']))
        script.write('clean\n')
        script.write('convert gpt\n')

        # System partition
        # NOTE: ESP needs to be >= 260 for Advanced Format 4K disks
        script.write('create partition efi size=500\n')
        script.write('format quick fs=fat32 label="System"\n')
        script.write('assign letter="S"\n')

        # Microsoft Reserved (MSR) partition
        script.write('create partition msr size=128\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format quick fs=ntfs label="Windows"\n')
        script.write('assign letter="W"\n')

        # Recovery Tools partition
        script.write('shrink minimum=500\n')
        script.write('create partition primary\n')
        script.write('format quick fs=ntfs label="Recovery Tools"\n')
        script.write('assign letter="T"\n')
        script.write('set id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"\n')
        script.write('gpt attributes=0x8000000000000001\n')

    # Run script
    run_program(['diskpart', '/s', DISKPART_SCRIPT])
    time.sleep(2)

def format_mbr(disk):
    """Format disk for use as a Windows OS disk using the MBR layout."""
    with open(DISKPART_SCRIPT, 'w') as script:
        # Partition table
        script.write('select disk {}\n'.format(disk['Number']))
        script.write('clean\n')

        # System partition
        script.write('create partition primary size=100\n')
        script.write('format fs=ntfs quick label="System Reserved"\n')
        script.write('active\n')
        script.write('assign letter="S"\n')

        # Windows partition
        script.write('create partition primary\n')
        script.write('format fs=ntfs quick label="Windows"\n')
        script.write('assign letter="W"\n')

        # Recovery Tools partition
        script.write('shrink minimum=500\n')
        script.write('create partition primary\n')
        script.write('format quick fs=ntfs label="Recovery"\n')
        script.write('assign letter="T"\n')
        script.write('set id=27\n')

    # Run script
    run_program(['diskpart', '/s', DISKPART_SCRIPT])
    time.sleep(2)

def mount_windows_share():
    """Mount the  Windows images share unless labeled as already mounted."""
    if WINDOWS_SERVER['Mounted']:
        # Blindly skip if we mounted earlier
        continue
    
    mount_network_share(WINDOWS_SERVER)

def select_windows_version():
    actions = [
        {'Name': 'Main Menu', 'Letter': 'M'},
        ]

    # Menu loop
    selection = menu_select(
        title = 'Which version of Windows are we installing?',
        main_entries = WINDOWS_VERSIONS,
        action_entries = actions)

    if selection.isnumeric():
        return WINDOWS_VERSIONS[int(selection)-1]
    elif selection == 'M':
        raise GeneralAbort

def setup_windows(windows_image, windows_version):
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'apply',
        windows_image['Path'],
        windows_version['Image Name'],
        'W:\\']
    if 'Glob' in windows_image:
        cmd.extend(windows_image['Glob'])
    run_program(cmd)

def setup_windows_re(windows_version, windows_letter='W', tools_letter='T'):
    win = r'{}:\Windows'.format(windows_letter)
    winre = r'{}\System32\Recovery\WinRE.wim'.format(win)
    dest = r'{}:\Recovery\WindowsRE'.format(tools_letter)
    
    # Copy WinRE.wim
    os.makedirs(dest, exist_ok=True)
    shutil.copy(winre, r'{}\WinRE.wim'.format(dest))
    
    # Set location
    cmd = [
        r'{}\System32\ReAgentc.exe'.format(win),
        '/setreimage',
        '/path', dest,
        '/target', win]
    run_program(cmd)

def update_boot_partition(system_letter='S', windows_letter='W', mode='ALL'):
    cmd = [
        r'{}:\Windows\System32\bcdboot.exe'.format(windows_letter),
        r'{}:\Windows'.format(windows_letter),
        '/s', '{}:'.format(system_letter),
        '/f', mode]
    run_program(cmd)

def wim_contains_image(filename, imagename):
    cmd = [
        global_vars['Tools']['wimlib-imagex'],
        'info',
        filename,
        imagename]
    try:
        run_program(cmd)
    except subprocess.CalledProcessError:
        return False
    
    return True

if __name__ == '__main__':
    print("This file is not meant to be called directly.")
